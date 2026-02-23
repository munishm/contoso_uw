// ============================================================================
// Contoso Bank IWPB Underwriting - Azure Infrastructure
// ============================================================================
// Resources:
//   - Azure Cosmos DB (NoSQL) - Case, Document, Entity, Summary storage
//   - Azure Blob Storage - Document file storage
//   - Azure Service Bus - Document processing queue
//   - Azure App Service - FastAPI application hosting
//   - Application Insights - Monitoring and telemetry
//   - Log Analytics Workspace - Centralized logging
// Environment: Development (POC)
// ============================================================================

@description('The environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('The Azure region for deployment')
param location string = resourceGroup().location

@description('Base name for all resources')
param baseName string = 'contoso-iwpb-uw'

@description('App Service Plan SKU')
@allowed(['B1', 'B2', 'B3', 'S1', 'S2', 'S3', 'P1v3', 'P2v3', 'P3v3'])
param appServicePlanSku string = 'B1'

@description('Python runtime version')
param pythonVersion string = '3.11'

@description('Service Bus SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param serviceBusSku string = 'Standard'

@description('Cosmos DB location (can be different from main location due to regional availability)')
param cosmosLocation string = 'westus2'

// ============================================================================
// Variables
// ============================================================================

var resourceSuffix = '${baseName}-${environment}'
var resourceSuffixClean = replace('${baseName}${environment}', '-', '')

// Resource names
var logAnalyticsName = 'log-${resourceSuffix}'
var appInsightsName = 'appi-${resourceSuffix}'
var cosmosAccountName = 'cosmos-${resourceSuffix}'
var storageAccountName = take('st${resourceSuffixClean}', 24) // Max 24 chars, alphanumeric only
var serviceBusNamespaceName = 'sb-${resourceSuffix}'
var appServicePlanName = 'plan-${resourceSuffix}'
var appServiceName = 'app-${resourceSuffix}'

// Cosmos DB configuration
var cosmosDatabaseName = 'underwriting'
var cosmosContainers = [
  { name: 'cases', partitionKey: '/case_id' }
  { name: 'documents', partitionKey: '/case_id' }
  { name: 'entities', partitionKey: '/document_id' }
  { name: 'summaries', partitionKey: '/document_id' }
  { name: 'counters', partitionKey: '/id' }
]

// Storage configuration
var blobContainerName = 'documents'

// Service Bus configuration
var serviceBusQueueName = 'document-processing'

var tags = {
  Environment: environment
  Project: 'CONTOSO-IWPB-UW'
  ManagedBy: 'Bicep'
  Application: 'Underwriting-API'
}

// ============================================================================
// Log Analytics Workspace
// ============================================================================

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: environment == 'dev' ? 1 : 5
    }
  }
}

// ============================================================================
// Application Insights
// ============================================================================

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    RetentionInDays: 30
  }
}

// ============================================================================
// Azure Cosmos DB Account (Serverless)
// ============================================================================

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: cosmosLocation
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: cosmosLocation
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    enableFreeTier: false
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false // Allow key-based auth for dev
  }
}

// Cosmos DB Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: cosmosDatabaseName
  properties: {
    resource: {
      id: cosmosDatabaseName
    }
  }
}

// Cosmos DB Containers
resource cosmosContainerResources 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = [for container in cosmosContainers: {
  parent: cosmosDatabase
  name: container.name
  properties: {
    resource: {
      id: container.name
      partitionKey: {
        paths: [container.partitionKey]
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/_etag/?'
          }
        ]
      }
      defaultTtl: -1 // No TTL by default
    }
    options: {
      throughput: 400 // Minimum RU/s for provisioned throughput
    }
  }
}]

// ============================================================================
// Azure Storage Account (Blob)
// ============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false // Disabled - using Azure AD auth via Managed Identity
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Blob Service
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

// Blob Container for documents
resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: blobContainerName
  properties: {
    publicAccess: 'None'
  }
}

// ============================================================================
// Azure Service Bus Namespace
// ============================================================================

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: serviceBusNamespaceName
  location: location
  tags: tags
  sku: {
    name: serviceBusSku
    tier: serviceBusSku
  }
  properties: {
    minimumTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false // Allow SAS auth for dev
  }
}

// Service Bus Queue for document processing
resource serviceBusQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBusNamespace
  name: serviceBusQueueName
  properties: {
    maxDeliveryCount: 10
    lockDuration: 'PT5M' // 5 minutes lock
    defaultMessageTimeToLive: 'P14D' // 14 days TTL
    deadLetteringOnMessageExpiration: true
    enablePartitioning: false
    requiresDuplicateDetection: false
    maxSizeInMegabytes: 1024
  }
}

// ============================================================================
// App Service Plan (Linux)
// ============================================================================

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  kind: 'linux'
  sku: {
    name: appServicePlanSku
    capacity: 1
  }
  properties: {
    reserved: true // Required for Linux
  }
}

// ============================================================================
// App Service (FastAPI Application)
// ============================================================================

resource appService 'Microsoft.Web/sites@2023-12-01' = {
  name: appServiceName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'PYTHON|${pythonVersion}'
      alwaysOn: appServicePlanSku != 'B1'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      healthCheckPath: '/health'
      appCommandLine: '/home/site/wwwroot/startup.sh'
      appSettings: [
        // Build settings
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'false'
        }
        {
          name: 'PYTHONPATH'
          value: '/home/site/wwwroot'
        }
        // Application settings
        {
          name: 'APP_ENV'
          value: environment
        }
        {
          name: 'DEBUG'
          value: environment == 'dev' ? 'true' : 'false'
        }
        {
          name: 'LOG_LEVEL'
          value: environment == 'dev' ? 'DEBUG' : 'INFO'
        }
        // Application Insights
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }
        // Cosmos DB
        {
          name: 'COSMOS_ENDPOINT'
          value: cosmosAccount.properties.documentEndpoint
        }
        {
          name: 'COSMOS_KEY'
          value: cosmosAccount.listKeys().primaryMasterKey
        }
        {
          name: 'COSMOS_DATABASE_NAME'
          value: cosmosDatabaseName
        }
        // Blob Storage (using Azure AD auth via Managed Identity)
        {
          name: 'BLOB_ACCOUNT_URL'
          value: 'https://${storageAccount.name}.blob.${az.environment().suffixes.storage}'
        }
        // Note: BLOB_CONNECTION_STRING removed - using Managed Identity instead
        {
          name: 'BLOB_CONTAINER_NAME'
          value: blobContainerName
        }
        // Service Bus
        {
          name: 'SERVICE_BUS_NAMESPACE'
          value: '${serviceBusNamespace.name}.servicebus.windows.net'
        }
        {
          name: 'SERVICE_BUS_CONNECTION_STRING'
          value: listKeys('${serviceBusNamespace.id}/AuthorizationRules/RootManageSharedAccessKey', serviceBusNamespace.apiVersion).primaryConnectionString
        }
        {
          name: 'SERVICE_BUS_QUEUE_NAME'
          value: serviceBusQueueName
        }
        // Logging
        {
          name: 'WEBSITE_HTTPLOGGING_RETENTION_DAYS'
          value: '7'
        }
      ]
    }
  }
}

// ============================================================================
// Role Assignments (Managed Identity)
// ============================================================================

// Storage Blob Data Contributor for App Service
resource storageBlobRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, appService.id, 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Service Bus Data Sender for App Service
resource serviceBusSenderRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, appService.id, '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39')
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39') // Azure Service Bus Data Sender
    principalId: appService.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// Diagnostic Settings
// ============================================================================

resource appServiceDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'appServiceDiagnostics'
  scope: appService
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      { category: 'AppServiceHTTPLogs', enabled: true }
      { category: 'AppServiceConsoleLogs', enabled: true }
      { category: 'AppServiceAppLogs', enabled: true }
      { category: 'AppServicePlatformLogs', enabled: true }
    ]
    metrics: [
      { category: 'AllMetrics', enabled: true }
    ]
  }
}

resource cosmosDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'cosmosDiagnostics'
  scope: cosmosAccount
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      { category: 'DataPlaneRequests', enabled: true }
      { category: 'QueryRuntimeStatistics', enabled: true }
    ]
    metrics: [
      { category: 'Requests', enabled: true }
    ]
  }
}

resource serviceBusDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'serviceBusDiagnostics'
  scope: serviceBusNamespace
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      { category: 'OperationalLogs', enabled: true }
    ]
    metrics: [
      { category: 'AllMetrics', enabled: true }
    ]
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('App Service name')
output appServiceName string = appService.name

@description('App Service URL')
output appUrl string = 'https://${appService.properties.defaultHostName}'

@description('Health endpoint')
output healthEndpoint string = 'https://${appService.properties.defaultHostName}/health'

@description('Swagger UI endpoint')
output swaggerEndpoint string = 'https://${appService.properties.defaultHostName}/docs'

@description('Cosmos DB account name')
output cosmosAccountName string = cosmosAccount.name

@description('Cosmos DB endpoint')
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint

@description('Storage account name')
output storageAccountName string = storageAccount.name

@description('Storage blob endpoint')
output storageBlobEndpoint string = storageAccount.properties.primaryEndpoints.blob

@description('Service Bus namespace')
output serviceBusNamespaceName string = serviceBusNamespace.name

@description('Service Bus queue name')
output serviceBusQueueName string = serviceBusQueueName

@description('Application Insights connection string')
output appInsightsConnectionString string = appInsights.properties.ConnectionString

@description('App Service Managed Identity Principal ID')
output appServicePrincipalId string = appService.identity.principalId
