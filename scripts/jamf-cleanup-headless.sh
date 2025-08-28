#!/bin/bash

# Headless version of delete_all script for GitHub Actions
# Removes all interactive prompts and uses environment variables

#Variable declarations
bearerToken=""
tokenExpirationEpoch="0"

# Check for required environment variables
if [ -z "$JAMF_URL" ] || [ -z "$JAMF_USERNAME" ] || [ -z "$JAMF_PASSWORD" ]; then
    echo "Error: Missing required environment variables"
    echo "Required: JAMF_URL, JAMF_USERNAME, JAMF_PASSWORD"
    exit 1
fi

jamfURL="$JAMF_URL"
apiUser="$JAMF_USERNAME"
apiPass="$JAMF_PASSWORD"

getBearerToken() {
    response=$(curl -s -u "$apiUser":"$apiPass" "$jamfURL"/api/v1/auth/token -X POST)
    bearerToken=$(echo "$response" | plutil -extract token raw -)
    if [ -z "$bearerToken" ] || [ "$bearerToken" = "null" ]; then
        echo "Error: Failed to obtain bearer token"
        exit 1
    fi
}

directory=$(dirname "$0")
objects=(buildings departments categories sites ldapservers userextensionattributes computerextensionattributes directorybindings diskencryptionconfigurations distributionpoints dockitems ibeacons packages printers removablemacaddresses scripts softwareupdateservers webhooks networksegments mobiledeviceextensionattributes usergroups classes advancedusersearches ebooks advancedcomputersearches computergroups computerinvitations licensedsoftware macapplications osxconfigurationprofiles policies restrictedsoftware advancedmobiledevicesearches mobiledeviceapplications mobiledeviceconfigurationprofiles mobiledevicegroups)

jamfhealthcheck(){
    if /usr/bin/curl -ksS "$jamfURL"/healthCheck.html | /usr/bin/grep -q "\\[\\]"
    then
        echo "Health Check: Passed"
        loginfo "$jamfURL Health Check: Passed"
    else
        echo "Health Check: FAILED. $jamfURL is not available. Exiting..."
        logalert "[Alert] $jamfURL Health Check: FAILED"
        exit 1
    fi
}

createfolders(){
    if [ ! -d "$directory/JSSResource" ]; then
        mkdir "$directory"/JSSResource
        for object in "${objects[@]}" 
        do
            mkdir -p "$directory"/JSSResource/"$object"
            echo "Created directory: $directory/JSSResource/$object"
        done
    fi
    if [ ! -d "$directory/objectID" ]; then
        mkdir -p "$directory"/objectID
    fi
}

object_id(){
    for file in "$directory"/objectID/*
    do
        indxnum=($(/bin/cat "$file"))
        if ! /bin/cat "$file" | /usr/bin/grep -q "XPath set is empty"
        then
            continue
        fi
    done
}

getid(){
    echo "Gathering object IDs..."
    
    for object in "${objects[@]}"
    do
        /usr/bin/curl -ksS -H "Accept: application/xml" -H "Authorization: Bearer ${bearerToken}" "$jamfURL"/JSSResource/"$object" | /usr/bin/xmllint -xpath "//id" - 2>&1 | /usr/bin/sed 's/<[^>]*>/ /g' > "$directory"/objectID/"$object".xml
    done
    
    echo "Found objects"
    object_id
}

delete_jamf_objects(){
    echo "Starting deletion of Jamf Pro objects from: $jamfURL"
    loginfo "OPTION: DELETE $jamfURL" 
    
    local total=0
    local successful=0
    local failures=0
    
    if [ ! -d "$directory"/objectID ]; then
        echo "No folder at $directory/objectID"
        echo "Creating folders and getting object IDs..."
        createfolders
        getid
    else
        getid
    fi
    
    # Delete app installer deployments first (API v1)
    echo "Deleting app installer deployments..."
    response=$(curl -s -H "Authorization: Bearer ${bearerToken}" -X GET "$jamfURL/api/v1/app-installers/deployments")
    idList=$(echo $response | grep -o '"id" : "[0-9]*"' | sed 's/"id" : "//;s/"//' | sort -u )
    for id in $idList; do
        response=$(curl -s -H "Authorization: Bearer ${bearerToken}" -X DELETE "$jamfURL/api/v1/app-installers/deployments/$id")
        if [[ $? -eq 0 ]]; then
            echo "Successfully deleted app installer: $id"
        else
            echo "Failed to delete app installer: $id"
        fi
    done
    
    # Delete JSS Resource objects
    echo "Deleting JSS Resource objects..."
    objectrecord=($(object_id))
    loginfo "$directory/objectID/ contains records for the following objects:"
    
    for file in "$directory"/objectID/*
    do
        objectdata=$(head -c 5 "$file")
        if [[ "$objectdata" == "XPath" ]]; then
            continue
        else
            object=$(/usr/bin/basename "$file" .xml)
            objectindex=($(< "$file"))
            loginfo "$file: ${objectindex[*]}"
            
            if [ ${#objectindex[@]} -gt 0 ]; then
                echo "Deleting $object objects: ${objectindex[*]}"
                for id in "${objectindex[@]}"
                do	
                    result=$(curl -sk -H "Accept: application/xml" -H "Authorization: Bearer ${bearerToken}" "$jamfURL"/JSSResource/"$object"/id/"$id" -X DELETE)
                    let total+=1
                    if [[ "$result" == "<?xml version"* ]]; then
                        echo "[Success]: $object/id/$id"
                        let successful+=1
                    else
                        echo "[Failure]: $object/id/$id"
                        loginfo "DELETE failed: /$object/id/$id.xml"
                        loginfo "Result = $result"
                        let failures+=1
                    fi
                done
            else
                echo "No $object objects found to delete"
            fi
        fi
    done
    
    echo "Deletion complete: $successful out of $total objects were successfully deleted and $failures failed"
    return 0
}

# Logging functions
logfile="/tmp/jamf_pro_cleanup_headless.log"
if [ -e "$logfile" ]; then
    /bin/rm -f "$logfile"
fi
/usr/bin/touch "$logfile"

logalert(){
    echo "$logtimestamp [ALERT] $1" >> "$logfile"
}

loginfo(){
    echo "$logtimestamp  [INFO] $1" >> "$logfile"
}

logstart(){
    logtimestamp="$(date +%Y-%m-%d\ %H:%M:%S)"
    echo "$logtimestamp [START] logging $(/usr/bin/basename "$0")..." >> "$logfile"
}

logstop(){
    echo "$logtimestamp [END] logging $(/usr/bin/basename "$0")..." >> "$logfile"
    echo "Log file available at: $logfile"
}

# Main execution
main(){
    echo "=== Jamf Pro Headless Cleanup Script ==="
    echo "Target Jamf Pro Server: $jamfURL"
    
    logstart
    createfolders
    jamfhealthcheck
    getBearerToken
    delete_jamf_objects
    delete_jamf_objects
    delete_jamf_objects
    logstop
    
    echo "=== Cleanup Complete ==="
}

# Run main function
main