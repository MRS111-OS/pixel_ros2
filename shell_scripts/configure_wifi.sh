#!/bin/bash

LOG_FILE="./configure_wifi.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Define Wi-Fi networks and passwords
declare -A WIFI_NETWORKS
WIFI_NETWORKS["Oplify-5G"]="Aioplify@25
WIFI_NETWORKS["ciscosb-robo"]="qwerty123"
WIFI_NETWORKS["Reynash"]="hellobye"

# Define priorities
declare -A WIFI_PRIORITIES
WIFI_PRIORITIES["Oplify-5G"]=5
WIFI_PRIORITIES["ciscosb-robo"]=0
WIFI_PRIORITIES["Reynash"]=10

log "Starting Wi-Fi configuration..."

for SSID in "${!WIFI_NETWORKS[@]}"; do
    PASSWORD="${WIFI_NETWORKS[$SSID]}"
    PRIORITY="${WIFI_PRIORITIES[$SSID]}"
    FOUND_PROFILE=""

    # Check if a connection already exists for this SSID
    while read PROFILE; do
        EXISTING_SSID=$(nmcli -g 802-11-wireless.ssid connection show "$PROFILE" 2>/dev/null)
        if [ "$EXISTING_SSID" = "$SSID" ]; then
            FOUND_PROFILE="$PROFILE"
            break
        fi
    done <<< "$(nmcli -g NAME connection show)"

    if [ -n "$FOUND_PROFILE" ]; then
        log "Found existing connection profile '$FOUND_PROFILE' for SSID '$SSID'."
        # Check current priority
        CURRENT_PRIORITY=$(nmcli -g connection.autoconnect-priority connection show "$FOUND_PROFILE" 2>/dev/null)
        if [ "$CURRENT_PRIORITY" != "$PRIORITY" ]; then
            log "Updating priority for '$FOUND_PROFILE' from $CURRENT_PRIORITY to $PRIORITY."
            nmcli connection modify "$FOUND_PROFILE" connection.autoconnect-priority "$PRIORITY"
        else
            log "Priority for '$FOUND_PROFILE' already set to $PRIORITY. No change."
        fi
    else
        log "No existing connection profile found for SSID '$SSID'. Adding new connection."
        PROFILE_NAME="$SSID"
        if nmcli connection add type wifi ifname "*" con-name "$PROFILE_NAME" ssid "$SSID" &&
           nmcli connection modify "$PROFILE_NAME" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PASSWORD" &&
           nmcli connection modify "$PROFILE_NAME" connection.autoconnect-priority "$PRIORITY"; then
            log "Successfully added new profile '$PROFILE_NAME' for SSID '$SSID' with priority $PRIORITY."
        else
            log "Failed to add Wi-Fi network '$SSID'."
        fi
    fi
done

log "Wi-Fi configuration completed."

# Verification step
log "Verifying configured Wi-Fi networks..."
for SSID in "${!WIFI_NETWORKS[@]}"; do
    FOUND_PROFILE=""
    while read PROFILE; do
        EXISTING_SSID=$(nmcli -g 802-11-wireless.ssid connection show "$PROFILE" 2>/dev/null)
        if [ "$EXISTING_SSID" = "$SSID" ]; then
            FOUND_PROFILE="$PROFILE"
            break
        fi
    done <<< "$(nmcli -g NAME connection show)"

    if [ -n "$FOUND_PROFILE" ]; then
        PRIORITY_SET=$(nmcli -g connection.autoconnect-priority connection show "$FOUND_PROFILE" 2>/dev/null)
        log "Verified: Profile '$FOUND_PROFILE' exists for SSID '$SSID' with priority $PRIORITY_SET."
    else
        log "Warning: No saved profile found for SSID '$SSID'."
    fi
done

log "Verification completed."

