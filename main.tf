## Root provider requirements
terraform {
  required_providers {
    jamfpro = {
      source  = "deploymenttheory/jamfpro"
      version = "~> 0.1.5"
    }
    jsc = {
      source = "danjamf/jsctfprovider"
      version = "0.0.5"
    }
  }
}

## Jamf Pro provider root configuration
provider "jamfpro" {
  jamfpro_instance_fqdn          = var.jamfpro_instance_url
  auth_method =               "basic" // oauth2
  basic_auth_username = var.jamfpro_username
  basic_auth_password = var.jamfpro_password
  client_id                   = var.jamfpro_client_id
  client_secret               = var.jamfpro_client_secret
  enable_client_sdk_logs                 = false
  hide_sensitive_data         = true # Hides sensitive data in logs
  token_refresh_buffer_period_seconds = 5 # minutes
  jamfpro_load_balancer_lock     = true
  mandatory_request_delay_milliseconds = 100
}

## Initialize Jamf Pro child modules
module "jamfpro_demo_config" {
  source = "./modules/jamfpro_demo_config/"
}

## Initialize Experience Jamf vignette modules
module "ej_base" {
  source = "./modules/experience_jamf_vignettes/ej_base"
}

module "ej_incident_response" {
  source = "./modules/experience_jamf_vignettes/ej_incident_response"
}

module "ej_mac_cis_benchmark" {
  source = "./modules/experience_jamf_vignettes/ej_mac_cis_benchmark"
}

module "ej_mobile_cis_benchmark" {
  source = "./modules/experience_jamf_vignettes/ej_mobile_cis_benchmark"
}

module "ej_secure_remote_access" {
  source = "./modules/experience_jamf_vignettes/ej_secure_remote_access"
}

## Initialize sandbox module
module "sandbox" {
  source = "./modules/sandbox"
}

## JSC provider root configuration
provider "jsc" {
  username   = var.radar_user
  password   = var.radar_pass
  #customerid = var.radar_customerid
}

## Initialiaze JSC child modules
module "jsc_demo_config" {
  source = "./modules/jsc_demo_config/"
  jamfpro_instance_url = var.jamfpro_instance_url
  radar_user = var.radar_user
  tje_okta_clientid = var.tje_okta_clientid
  tje_okta_orgdomain = var.tje_okta_orgdomain
  wizard_suffix = var.wizard_suffix
}