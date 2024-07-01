param subscriptionId string
param name string
param location string
param use32BitWorkerProcess bool
param ftpsState string
param storageAccountName string
param linuxFxVersion string
param sku string
param skuCode string
param workerSize string
param workerSizeId string
param numberOfWorkers string
param repoUrl string
param branch string
param oidcUserIdentityName string
param hostingPlanName string
param serverFarmResourceGroup string
param alwaysOn bool

var contentShare = 'brandonresumefunctionapp9b1f'

resource name_resource 'Microsoft.Web/sites@2022-03-01' = {
  name: name
  kind: 'functionapp,linux'
  location: location
  tags: {
    'hidden-link: /app-insights-resource-id': '/subscriptions/e8e99544-b709-42dc-a7ec-39fd252b3d3a/resourceGroups/Websites/providers/Microsoft.Insights/components/brandonresumefunctionapp'
  }
  properties: {
    name: name
    siteConfig: {
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
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: reference('microsoft.insights/components/brandonresumefunctionapp', '2015-05-01').ConnectionString
        }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${listKeys(resourceId('e8e99544-b709-42dc-a7ec-39fd252b3d3a','Websites','Microsoft.Storage/storageAccounts',storageAccountName),'2019-06-01').keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${listKeys(resourceId('e8e99544-b709-42dc-a7ec-39fd252b3d3a','Websites','Microsoft.Storage/storageAccounts',storageAccountName),'2019-06-01').keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: contentShare
        }
      ]
      cors: {
        allowedOrigins: [
          'https://portal.azure.com'
        ]
      }
      use32BitWorkerProcess: use32BitWorkerProcess
      ftpsState: ftpsState
      linuxFxVersion: linuxFxVersion
    }
    clientAffinityEnabled: false
    virtualNetworkSubnetId: null
    publicNetworkAccess: 'Enabled'
    httpsOnly: true
    serverFarmId: '/subscriptions/${subscriptionId}/resourcegroups/${serverFarmResourceGroup}/providers/Microsoft.Web/serverfarms/${hostingPlanName}'
  }
  dependsOn: [
    brandonresumefunctionapp
    hostingPlan
  ]
}

resource name_scm 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2022-09-01' = {
  parent: name_resource
  name: 'scm'
  properties: {
    allow: false
  }
}

resource name_ftp 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2022-09-01' = {
  parent: name_resource
  name: 'ftp'
  properties: {
    allow: false
  }
}

resource name_web 'Microsoft.Web/sites/sourcecontrols@2020-12-01' = {
  parent: name_resource
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

resource hostingPlan 'Microsoft.Web/serverfarms@2018-11-01' = {
  name: hostingPlanName
  location: location
  kind: 'linux'
  tags: null
  properties: {
    name: hostingPlanName
    workerSize: workerSize
    workerSizeId: workerSizeId
    numberOfWorkers: numberOfWorkers
    reserved: true
  }
  sku: {
    tier: sku
    name: skuCode
  }
  dependsOn: []
}

resource brandonresumefunctionapp 'microsoft.insights/components@2020-02-02-preview' = {
  name: 'brandonresumefunctionapp'
  location: 'australiaeast'
  tags: null
  properties: {
    ApplicationId: name
    Request_Source: 'IbizaWebAppExtensionCreate'
    Flow_Type: 'Redfield'
    Application_Type: 'web'
    WorkspaceResourceId: '/subscriptions/e8e99544-b709-42dc-a7ec-39fd252b3d3a/resourceGroups/DefaultResourceGroup-EAU/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-e8e99544-b709-42dc-a7ec-39fd252b3d3a-EAU'
  }
  dependsOn: [
    newWorkspaceTemplate
  ]
}

module newWorkspaceTemplate './nested_newWorkspaceTemplate.bicep' = {
  name: 'newWorkspaceTemplate'
  scope: resourceGroup(subscriptionId, 'DefaultResourceGroup-EAU')
  params: {}
}
