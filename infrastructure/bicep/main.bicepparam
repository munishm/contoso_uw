// ============================================================================
// Contoso Bank IWPB Underwriting - Bicep Parameters (Dev Environment)
// ============================================================================

using 'main.bicep'

param environment = 'dev'
param location = 'eastus'
param baseName = 'contoso-iwpb-uw'
param appServicePlanSku = 'B1'
param pythonVersion = '3.11'
param serviceBusSku = 'Standard'
