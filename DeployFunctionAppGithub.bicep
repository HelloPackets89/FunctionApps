param location string = resourceGroup().location
param name string = 'beeresumequery'
param repoUrl string
param branch string

resource storageaccount 'Microsoft.Storage/storageAccounts@2023-04-01' = {
  name: '${name}storage'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}
var StorageAccountPrimaryAccessKey = listKeys(storageaccount.id, storageaccount.apiVersion).keys[0].value

resource appinsights 'Microsoft.Insights/components@2020-02-02' ={
  name: '${name}appinsights'
  location: location
  kind: 'web'
  properties:{
    Application_Type: 'web'
    publicNetworkAccessForIngestion:'Enabled'
    publicNetworkAccessForQuery:'Enabled'
  }
}
var AppInsightsPrimaryAccessKey = appinsights.properties.InstrumentationKey

resource hostingplan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${name}hp'
  location: location
  kind: 'linux'
  properties: {
    reserved:true
  }
  sku:{
    name: 'Y1' //Consumption plan
  }
}

resource ResumeFunctionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${name}functionapp'
  location: location
  kind: 'functionapp'
  identity:{
    type:'SystemAssigned'
  }
  properties:{
    httpsOnly:true
    serverFarmId:hostingplan.id
    siteConfig:{
//      use32BitWorkerProcess:true //this allows me to use the FREEEEE tier
      alwaysOn:false
      linuxFxVersion: 'python|3.11'
      cors:{
        allowedOrigins: [
          'https://portal.azure.com'
        ]
      }
      appSettings:[
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: AppInsightsPrimaryAccessKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: 'InstrumentationKey=${AppInsightsPrimaryAccessKey}'
        }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageaccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${StorageAccountPrimaryAccessKey}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(storageaccount.name)
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageaccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${StorageAccountPrimaryAccessKey}'
        }
      ]
    }
  }
}

//setting up github actions

//This blocks the use of git to publish my azure app.. but not github actions?
resource blockgithub 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2022-09-01' = {
  parent: ResumeFunctionApp
  name: 'scm'
  properties: {
    allow: false
  }
}

//This blocks FTP from being used to publish my azure app
resource name_ftp 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2022-09-01' = {
  parent: ResumeFunctionApp
  name: 'ftp'
  properties: {
    allow: false
  }
}

resource githubactions 'Microsoft.Web/sites/sourcecontrols@2020-12-01' = {
  parent: ResumeFunctionApp
  name: 'web'
  properties: {
    repoUrl: repoUrl
    branch: branch
    isManualIntegration: false
    deploymentRollbackEnabled: false
    isMercurial: false
    isGitHubAction: true
    gitHubActionConfiguration: {
      generateWorkflowFile: true
      workflowSettings: {
        appType: 'functionapp'
        authType: 'oidc'
        publishType: 'code'
        os: 'linux'
        runtimeStack: 'python'
        workflowApiVersion: '2022-10-01'
        slotName: 'production'
        variables: {
          runtimeVersion: '3.11'
          clientId: reference(oidcUserIdentity.id, '2018-11-30').clientId
          tenantId: reference(oidcUserIdentity.id, '2018-11-30').tenantId
        }
      }
    }
  }
}


resource oidcUserIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: oidcUserIdentityName
  location: location
  properties: {}
  dependsOn: [
    name_resource
  ]
}

resource oidcUserIdentityName_id 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2022-01-31-preview' = {
  parent: oidcUserIdentity
  name: '${uniqueString(resourceGroup().id)}'
  properties: {
    audiences: [
      'api://AzureADTokenExchange'
    ]
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:HelloPackets89/FunctionApps:ref:refs/heads/main'
  }
}

resource id_name 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: name_resource
  name: guid(resourceGroup().id, deployment().name)
  properties: {
    roleDefinitionId: '/subscriptions/${subscription().subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/de139f84-1756-47ae-9be6-808fbbe84772'
    principalId: reference(oidcUserIdentity.id, '2018-11-30').principalId
    principalType: 'ServicePrincipal'
  }
}
