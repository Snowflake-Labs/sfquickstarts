$modules = @(
    @{ Name = "AzureAD"; InstallCommand = "Install-Module -Name AzureAD -RequiredVersion 2.0.2.182 -Force -Scope CurrentUser -AllowClobber -Verbose" },
    @{ Name = "Az.Resources"; InstallCommand = "Install-Module -Name Az.Resources -RequiredVersion 7.8.0 -Force -Scope CurrentUser -Verbose" }
)

foreach ($module in $modules) {
    if (-not (Get-Module -ListAvailable -Name $module.Name)) {
        try {
            Invoke-Expression $module.InstallCommand
        } catch {
            Write-Host "Warning: Failed to install $($module.Name). Continuing..."
        }
    }
}

Connect-AzureAD
Connect-AzAccount
 
$resourceAppName = Read-Host "Enter Resource App Name"
$clientAppName = Read-Host "Enter Client App Name"
$roleName = Read-Host "Enter App Role Name"
$tenantId = Read-Host "Enter Tenant ID"



$resourceApp = New-AzADApplication -DisplayName $resourceAppName
Start-Sleep -Seconds 10
$resourceAppId = $resourceApp.AppId
$resourceObjectId = $resourceApp.Id

Write-Host "Resource App created: $resourceAppId"


$clientApp = New-AzADApplication -DisplayName $clientAppName
Start-Sleep -Seconds 10
$clientAppId = $clientApp.AppId
$clientAppObjectId = $clientApp.Id
Write-Host "Client App created: $clientAppId"


#expose resource app api
$identifierUri = "api://$resourceAppId"
Set-AzADApplication -ObjectId $resourceApp.Id  -IdentifierUris $identifierUri

$startDate = Get-Date
$endDate = $startDate.AddYears(1)
$secret = New-AzureADApplicationPasswordCredential -ObjectId $clientApp.Id -CustomKeyIdentifier "SnowflakeSecret$day$hour$min" -StartDate $startDate -EndDate $endDate #Create client secret
Write-Host "secret created = "$secret.Value


$graphAndAzResourceModules = @(
 
    @{ Name = "Microsoft.Graph.Authentication"; InstallCommand = "Install-Module -Name Microsoft.Graph.Authentication -RequiredVersion 2.25.0 -Force -Scope CurrentUser -Verbose" },
    @{ Name = "Microsoft.Graph.Applications"; InstallCommand = "Install-Module -Name Microsoft.Graph.Applications -RequiredVersion 2.25.0 -Force -Scope CurrentUser -Verbose" },
    @{ Name = "Microsoft.Graph.Identity.SignIns"; InstallCommand = "Install-Module -Name Microsoft.Graph.Identity.SignIns -RequiredVersion 2.25.0 -Force -Scope CurrentUser -Verbose" }
    
)

foreach ($module in $graphAndAzResourceModules) {
    if (-not (Get-Module -ListAvailable -Name $module.Name)) {
        try {
            Invoke-Expression $module.InstallCommand
        } catch {
            Write-Host "Warning: Failed to install $($module.Name). Continuing..."
        }
    }
}
Connect-MgGraph


#create app role
$appRole = New-Object Microsoft.Open.MSGraph.Model.AppRole
$appRole.AllowedMemberTypes = New-Object System.Collections.Generic.List[string]
$appRole.AllowedMemberTypes.Add(“Application”)
$appRole.DisplayName = $roleName
$appRole.Id = New-Guid
$appRole.IsEnabled = $true
$appRole.Description = "Snowflake app role"
$appRole.Value = "session:role:"+$roleName;

$appObjectId = $resourceApp.Id
$app = Get-AzureADMSApplication -ObjectId $appObjectId
$appRoles = $app.AppRoles
#Write-Host “App Roles before addition of new role..”
#Write-Host $appRoles
$appRoles.Add($appRole)
Set-AzureADMSApplication -ObjectId $app.Id -AppRoles $appRoles


#create api role/scope
$scopes = New-Object System.Collections.Generic.List[Microsoft.Open.MsGraph.Model.PermissionScope]

$scope = New-Object Microsoft.Open.MsGraph.Model.PermissionScope
        $scope.Id = New-Guid
        $scope.Value = "session:scope:"+$roleName
        $scope.UserConsentDisplayName = "null"
        $scope.UserConsentDescription = "null"
        $scope.AdminConsentDisplayName = "Account Admin"
        $scope.AdminConsentDescription = "Can administer the Snowflake account"
        $scope.IsEnabled = $true
        $scope.Type = "User"


$scopes.Add($scope)
$app.Api.Oauth2PermissionScopes = $scopes
Set-AzureADMSApplication -ObjectId $app.Id -Api $app.Api
Write-Host "scope '$($scope)' added"



$resourceApp = Get-AzureADMSApplication | Where-Object { $_.DisplayName -eq $resourceAppName }


$resourceSP = Get-AzADServicePrincipal -ApplicationId $resourceAppId
if (-not $resourceSP) {
    Write-Host "Creating missing resource service principal..."
    New-AzADServicePrincipal -ApplicationId $resourceAppId
    Start-Sleep -Seconds 10  # Wait for propagation
    $resourceSP = Get-AzADServicePrincipal -ApplicationId $resourceAppId
}

$clientSP = Get-AzADServicePrincipal -ApplicationId $clientAppId
if (-not $clientSP) {
    Write-Host "Creating missing client service principal..."
    New-AzADServicePrincipal -ApplicationId $clientAppId
    Start-Sleep -Seconds 10  # Wait for propagation
    $clientSP = Get-AzADServicePrincipal -ApplicationId $clientAppId
}


Write-Host $clientSP.Id
Write-Host $resourceSP.Id

# Assign the app role to client sp
$appRole = $resourceApp.AppRoles | Where-Object { $_.Value -eq "session:role:"+$roleName }
$params = @{
principalId = $clientSP.Id
resourceId = $resourceSP.Id
appRoleId = $appRole.Id
}

New-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $clientSP.Id -BodyParameter $params
Start-Sleep -Seconds 10  # Wait for propagation

# Assign the delegated api permission




$resourceSP = Get-MgServicePrincipal -Filter "AppId eq '$resourceAppId'"
$resourceOAuthPermissions = $resourceSP.Oauth2PermissionScopes
$selectedScope = $resourceOAuthPermissions | Where-Object { $_.Value -contains "session:scope:"+$roleName}
Write-Host $selectedScope.Id


$grantBody = @{
    clientId   = $clientSP.Id
    consentType = "AllPrincipals"
    resourceId  = $resourceSP.Id
    scope       = $selectedScope.Value
}

New-MgOauth2PermissionGrant -BodyParameter $grantBody





#configure the scope and role for app
$requiredResourceAccess = @(
    @{
        resourceAppId = $resourceSP.AppId
        resourceAccess = @(
            @{
                id   = $selectedScope.Id   # Replace with actual scope GUID
                type = "Scope"           # Use "Scope" for Delegated Permissions
            },
            @{
                id   = $appRole.Id   # Replace with actual app role GUID
                type = "Role"              # Use "Role" for Application Permissions
            }
        )
    }
)

Update-MgApplication -ApplicationId $clientApp.Id -RequiredResourceAccess $requiredResourceAccess




$body = @{
    client_secret = $secret.Value
    client_id     = $clientAppId
    scope         = "$resourceAppId/.default"
    grant_type    = "client_credentials"
}

$tokenResponse = Invoke-RestMethod -Method Post -Uri "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token" -Body $body
$accessToken = $tokenResponse.access_token

Write-Host "Access Token: $accessToken"



$tokenParts = $accessToken -split '\.'

$payload=$tokenParts[1]


$decodedPayload = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload))
$payloadObject = $decodedPayload | ConvertFrom-Json

Write-Host $payloadObject

# Extract the 'sub' attribute
$sub = $payloadObject.sub
$sub





# Define the file path (same directory as the script)
$desktopPath = [System.Environment]::GetFolderPath("Desktop")
$outputFile = "$desktopPath\snowflakeinfo.txt"

$clientSecretValue = $secret.Value
# Format the content
$Data = @"
============================================================================================================================
Snowflake power platform connection info
============================================================================================================================
Tenant: $TenantId
Client ID: $clientAppId
Client Secret : $clientSecretValue
Resource URL: $resourceAppId


============================================================================================================================
Snowflake SQL Commands. Please execute these commands on Snowflake for adding Security Integration and Creating User, Role
============================================================================================================================
create security integration external_azure_delegated
    type = external_oauth
    enabled = true
    external_oauth_any_role_mode = 'ENABLE'
    external_oauth_type = azure
    external_oauth_issuer = 'https://sts.windows.net/$TenantId/'
    external_oauth_jws_keys_url = 'https://login.microsoftonline.com/$TenantId/discovery/v2.0/keys'
    external_oauth_audience_list = ('$resourceAppId')
    external_oauth_token_user_mapping_claim = (upn,sub)
    external_oauth_snowflake_user_mapping_attribute = 'login_name';



ALTER ACCOUNT SET EXTERNAL_OAUTH_ADD_PRIVILEGED_ROLES_TO_BLOCKED_LIST = FALSE;

CREATE OR REPLACE USER AAD_SP_USER
	            LOGIN_NAME = '$sub' 
	            DISPLAY_NAME = 'AAD_SP_USER' 
	            COMMENT = 'Snowflake User';

CREATE ROLE IF NOT EXISTS $roleName;


GRANT ROLE $roleName TO USER AAD_SP_USER;

"@

# Write to file
$Data | Out-File -FilePath $outputFile -Encoding UTF8

Write-Host "Info saved to: $outputFile"
