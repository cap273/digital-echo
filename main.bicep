param location string = resourceGroup().location

@secure()
param openAIAPIKey string

@secure()
param elevenlabsAPIKey string

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-04-01' = {
  name: 'chatgptstorage57382'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
  }
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2022-09-01' = {
  name: 'default'
  parent: storageAccount
}

resource personasContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: 'personas'
  parent: blobServices
  properties: {
    publicAccess: 'None'
  }
}

resource audiofilesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: 'audiofiles'
  parent: blobServices
  properties: {
    publicAccess: 'Blob'
  }
}

resource staticfilesContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: 'static'
  parent: blobServices
  properties: {
    publicAccess: 'Blob'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2021-01-01' = {
  name: 'chatgpt-functionapp-plan-2'
  location: location
  kind: 'linux'
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2018-11-01' = {
  name: 'chatgpt-functionapp-2'
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.10'
      ftpsState: 'FtpsOnly'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'AzureStorageAccountConnectionString'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'AzureServiceBusConnectionString'
          value: 'Endpoint=sb://${serviceBusNamespace.name}.servicebus.windows.net/;SharedAccessKeyName=${serviceBusAuthorizationRule.name};SharedAccessKey=${listKeys('${serviceBusNamespace.id}/AuthorizationRules/${serviceBusAuthorizationRule.name}', serviceBusNamespace.apiVersion).primaryKey}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower('chatgpt-functionapp-2')
        }
        {
          name: 'OPENAI_API_KEY'
          value: openAIAPIKey
        }
        {
          name: 'ELEVENLABS_API_KEY'
          value: elevenlabsAPIKey
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: applicationInsights.properties.InstrumentationKey
        }
        {
          name: 'STORAGE_ACCOUNT_NAME'
          value: storageAccount.name
        }
        {
          name: 'AUDIOFILES_CONTAINER_NAME'
          value: audiofilesContainer.name
        }
        {
          name: 'PERSONAS_CONTAINER_NAME'
          value: personasContainer.name
        }
      ]
    }
    
  }
}

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2021-06-01-preview' = {
  name: 'chatgpt-servicebus-2'
  location: location
  sku: {
    name: 'Standard'
  }
}

resource serviceBusAuthorizationRule 'Microsoft.ServiceBus/namespaces/AuthorizationRules@2022-10-01-preview' = {
  name: 'manage-policy'
  parent: serviceBusNamespace
  properties: {
    rights: [
      'Listen'
      'Send'
      'Manage'
    ]
  }
}

resource chatgptTopic 'Microsoft.ServiceBus/namespaces/topics@2021-06-01-preview' = {
  parent: serviceBusNamespace
  name: 'chatgpt'
}

resource toChatGPTSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  name: 'to_chatgpt'
  parent: chatgptTopic
}

resource elevenlabsTopic 'Microsoft.ServiceBus/namespaces/topics@2021-06-01-preview' = {
  parent: serviceBusNamespace
  name: 'elevenlabs'
}

resource toElevenLabsSubscription 'Microsoft.ServiceBus/namespaces/topics/subscriptions@2022-10-01-preview' = {
  name: 'to_elevenlabs'
  parent: elevenlabsTopic
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-12-01-preview' = {
  name: 'gpt-loganalitics'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'gpt-appinsights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

resource appServicePlanFrontend 'Microsoft.Web/serverfarms@2021-01-01' = {
  name: 'chatgpt-frontend-plan-2'
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true
  }
  kind: 'linux'
}

resource appService 'Microsoft.Web/sites@2020-06-01' = {
  name: 'personachat'
  location: location
  kind: 'web'
  properties: {
    serverFarmId: appServicePlanFrontend.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      ftpsState: 'FtpsOnly'
      appSettings: [
        {
          name: 'AZURE_FUNCTIONS_NAME'
          value: functionApp.name
        }
      ]
    }
  }
}




