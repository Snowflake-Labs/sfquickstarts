$modules = @(
    @{ Name = "Microsoft.Graph.Authentication"; InstallCommand = "Install-Module -Name Microsoft.Graph.Authentication -Force -Scope CurrentUser -Verbose" },
    @{ Name = "Microsoft.Graph.Applications"; InstallCommand = "Install-Module -Name Microsoft.Graph.Applications -Force -Scope CurrentUser -Verbose" },
    @{ Name = "Microsoft.Graph.Identity.SignIns"; InstallCommand = "Install-Module -Name Microsoft.Graph.Identity.SignIns -Force -Scope CurrentUser -Verbose" }
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

# Connect to Microsoft Graph with required scopes
Connect-MgGraph -Scopes "Application.ReadWrite.All", "Directory.ReadWrite.All" -TenantId $tenantId
 
$resourceAppName = Read-Host "Enter Resource App Name"
$clientAppName = Read-Host "Enter Client App Name"
$roleName = Read-Host "Enter App Role Name"
$tenantId = Read-Host "Enter Tenant ID"

# Create resource application
$resourceAppParams = @{
    DisplayName = $resourceAppName
    SignInAudience = "AzureADMyOrg"
}
$resourceApp = New-MgApplication @resourceAppParams
Start-Sleep -Seconds 10
$resourceAppId = $resourceApp.AppId
$resourceObjectId = $resourceApp.Id

Write-Host "Resource App created: $resourceAppId"

# Create client application
$clientAppParams = @{
    DisplayName = $clientAppName
    SignInAudience = "AzureADMyOrg"
}
$clientApp = New-MgApplication @clientAppParams
Start-Sleep -Seconds 10
$clientAppId = $clientApp.AppId
$clientObjectId = $clientApp.Id
Write-Host "Client App created: $clientAppId"

# Set identifier URI for resource app
$identifierUri = "api://$resourceAppId"
Update-MgApplication -ApplicationId $resourceApp.Id -IdentifierUris @($identifierUri)

# Create client secret
$passwordCredential = @{
    DisplayName = "SnowflakeSecret"
    EndDateTime = (Get-Date).AddYears(1)
}
$secret = Add-MgApplicationPassword -ApplicationId $clientApp.Id -PasswordCredential $passwordCredential
Write-Host "Secret created = $($secret.SecretText)"

# Create app role
$appRole = @{
    AllowedMemberTypes = @("Application")
    Description = "Snowflake app role"
    DisplayName = $roleName
    Id = [Guid]::NewGuid()
    IsEnabled = $true
    Value = "session:role:$roleName"
}

# Get existing app roles and add new one
$existingApp = Get-MgApplication -ApplicationId $resourceApp.Id
$appRoles = $existingApp.AppRoles + $appRole
Update-MgApplication -ApplicationId $resourceApp.Id -AppRoles $appRoles

# Create API permission scope
$scope = @{
    Id = [Guid]::NewGuid()
    Value = "session:scope:$roleName"
    AdminConsentDescription = "Can administer the Snowflake account"
    AdminConsentDisplayName = "Account Admin"
    IsEnabled = $true
    Type = "Admin"
}

$api = @{
    Oauth2PermissionScopes = @($scope)
}
Update-MgApplication -ApplicationId $resourceApp.Id -Api $api

# Create service principals
$resourceSP = New-MgServicePrincipal -AppId $resourceAppId
Start-Sleep -Seconds 10

$clientSP = New-MgServicePrincipal -AppId $clientAppId
Start-Sleep -Seconds 10

# Assign app role
$appRoleAssignment = @{
    PrincipalId = $clientSP.Id
    ResourceId = $resourceSP.Id
    AppRoleId = $appRole.Id
}
New-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $clientSP.Id -BodyParameter $appRoleAssignment

# Grant OAuth2 permission
$permissionGrant = @{
    ClientId = $clientSP.Id
    ConsentType = "AllPrincipals"
    ResourceId = $resourceSP.Id
    Scope = $scope.Value
}
New-MgOauth2PermissionGrant -BodyParameter $permissionGrant

# Configure required resource access
$requiredResourceAccess = @{
    ResourceAppId = $resourceAppId
    ResourceAccess = @(
        @{
            Id = $scope.Id
            Type = "Scope"
        },
        @{
            Id = $appRole.Id
            Type = "Role"
        }
    )
}
Update-MgApplication -ApplicationId $clientApp.Id -RequiredResourceAccess @($requiredResourceAccess)

# Get access token
$tokenUrl = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"
$body = @{
    client_id = $clientAppId
    client_secret = $secret.SecretText
    scope = "$resourceAppId/.default"
    grant_type = "client_credentials"
}

$tokenResponse = Invoke-RestMethod -Method Post -Uri $tokenUrl -Body $body
$accessToken = $tokenResponse.access_token
Write-Host "Access Token: $accessToken"

# Decode token
$tokenParts = $accessToken -split '\.'
$payload = $tokenParts[1]
# Add padding to the payload
switch ($payload.Length % 4) {
    2 { $payload += '==' }
    3 { $payload += '=' }
}
$decodedPayload = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload))
$payloadObject = $decodedPayload | ConvertFrom-Json
$sub = $payloadObject.sub

# Save output to file
$desktopPath = [System.Environment]::GetFolderPath("Desktop")
$outputFile = "snowflakeinfo.txt"

$outputContent = @"
============================================================================================================================
Snowflake power platform connection info
============================================================================================================================
Tenant: $TenantId
Client ID: $clientAppId
Client Secret: $($secret.SecretText)
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

$outputContent | Out-File -FilePath $outputFile -Encoding UTF8
Write-Host "Info saved to: $outputFile"
