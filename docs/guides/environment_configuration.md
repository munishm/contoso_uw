# Environment Configuration Guide

This guide explains how to manage environment-specific configurations in the Contoso Bank Insurance Underwriting monorepo.

## Overview

Environment configurations are managed through `.env` files that store environment-specific settings, credentials, and feature flags. This approach enables:

- **Separation of configuration from code**: No hardcoded credentials or settings in source code
- **Environment-specific deployments**: Different settings for development, staging, and production
- **Security**: Sensitive credentials are never committed to version control
- **Flexibility**: Easy to modify settings without code changes

## File Structure

```
/
├── .env.example        # Template with all available variables (COMMITTED)
├── .env.dev            # Development environment (GITIGNORED)
├── .env.staging        # Staging environment (GITIGNORED)
├── .env.prod           # Production environment (GITIGNORED)
└── src/shared/config/
    └── env_loader.py   # Configuration loader utility
```

## Setup Instructions

### 1. Create Your Environment File

Copy the template to create your environment-specific file:

```bash
# For development
cp .env.example .env.dev

# For staging
cp .env.example .env.staging

# For production
cp .env.example .env.prod
```

### 2. Fill in Actual Values

Edit your newly created `.env.*` file and replace placeholder values with actual credentials:

```bash
# Example for .env.dev
vim .env.dev
```

**Important**: Never commit `.env.dev`, `.env.staging`, or `.env.prod` to version control. These files are already included in `.gitignore`.

### 3. Loading Configuration in Code

Use the `EnvironmentConfig` class from `src/shared/config/env_loader.py`:

```python
from shared.config.env_loader import EnvironmentConfig

# Load development environment
config = EnvironmentConfig.load(".env.dev")

# Access configuration values
azure_endpoint = config.get("AZURE_OPENAI_ENDPOINT")
debug_mode = config.get("DEBUG", default=False)

# Get required values (raises error if missing)
api_key = config.get("AZURE_OPENAI_API_KEY")
```

## Configuration Categories

### Application Settings

Basic application configuration:

- `APP_NAME`: Application identifier
- `APP_ENV`: Environment name (development, staging, production)
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Azure Settings

Azure subscription and resource group information:

- `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID
- `AZURE_RESOURCE_GROUP`: Resource group name
- `AZURE_TENANT_ID`: Azure AD tenant ID

### Azure AI Services

Configuration for Azure AI services:

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `AZURE_OPENAI_API_KEY`: API key for authentication
- `AZURE_OPENAI_DEPLOYMENT`: Deployment/model name
- `AZURE_OPENAI_API_VERSION`: API version (e.g., 2024-02-15-preview)

### Azure Storage

Azure Blob Storage configuration:

- `AZURE_STORAGE_ACCOUNT_NAME`: Storage account name
- `AZURE_STORAGE_CONTAINER_NAME`: Container for documents
- `AZURE_STORAGE_CONNECTION_STRING`: Full connection string

### Azure Cosmos DB

Database configuration:

- `AZURE_COSMOS_ENDPOINT`: Cosmos DB endpoint URL
- `AZURE_COSMOS_KEY`: Cosmos DB access key
- `AZURE_COSMOS_DATABASE`: Database name
- `AZURE_COSMOS_CONTAINER`: Container/collection name

### Component Configuration

Settings for AI components:

- `DOCUMENT_CLASSIFICATION_MODEL`: Model for classification
- `ENTITY_EXTRACTION_MODEL`: Model for entity extraction
- `DOCUMENT_SUMMARIZATION_MODEL`: Model for summarization

### Performance Settings

Performance tuning parameters:

- `MAX_WORKERS`: Maximum concurrent workers
- `BATCH_SIZE`: Batch processing size
- `TIMEOUT_SECONDS`: Operation timeout

### Feature Flags

Enable/disable features:

- `ENABLE_HUMAN_IN_LOOP`: Enable HITL approval workflows
- `ENABLE_AUDIT_LOGGING`: Enable audit trail logging
- `ENABLE_PERFORMANCE_MONITORING`: Enable performance metrics

## Environment-Specific Best Practices

### Development (.env.dev)

- Use lower resource limits (MAX_WORKERS=2, BATCH_SIZE=5)
- Enable debug mode (DEBUG=true, LOG_LEVEL=DEBUG)
- Use development Azure resources
- Enable all feature flags for testing

### Staging (.env.staging)

- Use production-like resource limits
- Disable debug mode (DEBUG=false, LOG_LEVEL=INFO)
- Use staging Azure resources
- Mirror production feature flags

### Production (.env.prod)

- Use optimized resource limits (MAX_WORKERS=8, BATCH_SIZE=20)
- Disable debug mode (DEBUG=false, LOG_LEVEL=WARNING)
- Use production Azure resources
- **Use Azure Key Vault for secrets** (see Security Considerations)

## Security Considerations

### For Development and Staging

- Store credentials in `.env.*` files (gitignored)
- Never commit these files to version control
- Share credentials securely through team channels (e.g., Azure Key Vault, 1Password)

### For Production

**Critical**: Production credentials MUST be managed through Azure Key Vault, not `.env` files.

1. **Store secrets in Azure Key Vault**:
   ```bash
   az keyvault secret set --vault-name contoso-uw-prod-kv \
     --name "AzureOpenAIKey" --value "actual-key"
   ```

2. **Reference Key Vault in code**:
   ```python
   from azure.identity import DefaultAzureCredential
   from azure.keyvault.secrets import SecretClient

   credential = DefaultAzureCredential()
   client = SecretClient(vault_url="https://contoso-uw-prod-kv.vault.azure.net/", 
                        credential=credential)
   
   api_key = client.get_secret("AzureOpenAIKey").value
   ```

3. **Use managed identities**: Configure Azure managed identities for production deployments to avoid storing any credentials.

## Validation

Validate your environment configuration:

```bash
# Test loading your environment
python3 -c "from shared.config.env_loader import EnvironmentConfig; \
            config = EnvironmentConfig.load('.env.dev'); \
            print('Configuration loaded successfully')"
```

## Troubleshooting

### "Configuration file not found"

Ensure you've created the `.env.*` file from the template:
```bash
cp .env.example .env.dev
```

### "Missing required variable"

Check that all required variables are set in your `.env.*` file. Compare against `.env.example` to see what's missing.

### "Azure authentication failed"

Verify your Azure credentials are correct:
```bash
az login
az account show
```

## Related Documentation

- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Python dotenv Package](https://github.com/theskumar/python-dotenv)
- [Shared Configuration Module](../../src/shared/config/README.md)

## Support

For questions about environment configuration:
- Check the [CONTRIBUTING.md](../../CONTRIBUTING.md) guide
- Review [ADR-004: Environment Configuration Strategy](../adr/004-environment-configuration.md)
- Contact the DevOps team
