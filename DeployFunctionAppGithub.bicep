param location string = resourceGroup().location
param name string = 'ballmarktest1'
param repoUrl string = 'https://github.com/HelloPackets89/FunctionApps'
param branch string = 'main'
param SPSecret string 
param tenantID string
param SPID string

//param githubsubject string = 'repo:HelloPackets89/FunctionApps:environment:Production'


resource storageaccount 'Microsoft.Storage/storageAccounts@2023-04-01' = {
  name: '${name}storage'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}
var StorageAccountPrimaryAccessKey = storageaccount.listKeys().keys[0].value

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
      linuxFxVersion: 'python|3.10'
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

/*/////setting up github actions

//This blocks the use of git to publish my azure app.. but not github actions?
resource blockgithub 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2022-09-01' = {
  parent: ResumeFunctionApp
  name: 'scm'
  properties: {
    allow: false
  }
}

/This blocks FTP from being used to publish my azure app
resource name_ftp 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2022-09-01' = {
  parent: ResumeFunctionApp
  name: 'ftp'
  properties: {
    allow: false
  }
}

resource oidcUserIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: '${name}identity'
  location: location
  dependsOn: [
    ResumeFunctionApp
  ]
}

resource oidcUserIdentityName_id 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2022-01-31-preview' = {
  parent: oidcUserIdentity
  name: uniqueString(resourceGroup().id)
  properties: {
    audiences: [
      'api://AzureADTokenExchange'
    ]
    issuer: 'https://token.actions.githubusercontent.com'
    subject: githubsubject
  }
}


/* de139f84-1756-47ae-9be6-808fbbe84772 refers to the built-in Website contributor role. 
This resource block assigns the Website Contributor role to our new identity which allows it to deploy resources 
within our scope. 'existing' forces a deployment error if the resource can't be found as opposed to just creating it +/

resource WebsiteContributor 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: 'de139f84-1756-47ae-9be6-808fbbe84772'
}

resource id_name 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: ResumeFunctionApp
  name: guid(resourceGroup().id, deployment().name)
  properties: {
    roleDefinitionId: WebsiteContributor.id
    principalId: oidcUserIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}


*/

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
  }
}
}

/*
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
     /* workflowSettings: {
        appType: 'functionapp'
        authType: 'serviceprincipal'
        publishType: 'code'
        os: 'linux'
        runtimeStack: 'python'
        workflowApiVersion: '2022-10-01'
        slotName: 'production'
        variables: {
          runtimeVersion: '3.11'
          clientId: SPID
          tenantId: tenantID
          clientSecret: SPSecret
        }
      }
    }
  }
}

resource githubactions 'Microsoft.Web/sites/sourcecontrols@2022-09-01' = {
  name: 'web'
  parent: ResumeFunctionApp
  properties: {
    branch: branch
    deploymentRollbackEnabled: false
    gitHubActionConfiguration: {
      codeConfiguration: {
        runtimeStack: 'python'
        runtimeVersion: '3.10'
      }
      generateWorkflowFile: true
      isLinux: true
    }
    isGitHubAction: true
    isManualIntegration: false
    isMercurial: false
    repoUrl: repoUrl
  }
}
  */
