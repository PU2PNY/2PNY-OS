save_secondary() (
  local ssid="$1" pass="$2" bssid="${3:-}" iface hidden=yes
  local cand=PU2PNY-WIFI-SECONDARY-CANDIDATE backup=PU2PNY-WIFI-SECONDARY-BACKUP
  local candidate_uuid="" committed=0
  test -n "$ssid" || { echo "Informe o SSID da rede Wi-Fi 2." >&2; exit 2; }
  [[ -z "$bssid" || "$bssid" =~ ^([[:xdigit:]]{2}:){5}[[:xdigit:]]{2}$ ]] || { echo "BSSID inválido." >&2; exit 2; }
  if test "$ssid" = "$(profile_ssid "$PRIMARY")"; then
    echo "Escolha uma rede diferente da Rede Wi-Fi 1." >&2
    exit 2
  fi
  iface="$(wifi_if)"
  test -n "$iface" || { echo "Interface Wi-Fi não encontrada." >&2; exit 3; }
  if test -n "$bssid" || nm -t --escape no -f SSID device wifi list --rescan no 2>/dev/null | grep -Fxq -- "$ssid"; then hidden=no; fi

  save_nm(){ timeout -k 1 5 /usr/bin/nmcli "$@" >/dev/null 2>&1; }
  cleanup(){
    if test "$committed" = 1; then return; fi
    if test -n "$candidate_uuid"; then save_nm connection delete uuid "$candidate_uuid" || true
    else save_nm connection delete "$cand" || true
    fi
    if exists "$backup" && ! exists "$SECONDARY"; then
      save_nm connection modify "$backup" connection.id "$SECONDARY" || true
    fi
  }
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM

  # Recover an interrupted rename before staging another candidate.
  save_nm connection delete "$cand" || true
  if exists "$backup"; then
    if exists "$SECONDARY"; then
      if test "$(active_name)" = "$backup"; then
        echo "A conexão ativa usa o perfil Wi-Fi anterior. Aguarde a reconexão antes de trocar a rede de backup." >&2
        exit 6
      fi
      save_nm connection delete "$backup"
    else save_nm connection modify "$backup" connection.id "$SECONDARY"
    fi
  fi
  # Create the candidate disabled so an active Wi-Fi session stays up.
  save_nm connection add type wifi ifname "$iface" con-name "$cand" ssid "$ssid" connection.autoconnect no ||
    { echo "Não foi possível criar o perfil da Rede Wi-Fi 2." >&2; exit 4; }
  candidate_uuid="$(profile_uuid "$cand")"
  test -n "$candidate_uuid" || { echo "O NetworkManager não confirmou o perfil." >&2; exit 4; }
  save_nm connection modify uuid "$candidate_uuid" connection.autoconnect-priority 75 connection.autoconnect-retries 2 connection.mdns yes \
    802-11-wireless.hidden "$hidden" 802-11-wireless.powersave 2 802-11-wireless.cloned-mac-address permanent \
    ipv4.method auto ipv4.dhcp-timeout 20 ipv4.route-metric 50 ipv6.method auto ||
    { echo "Não foi possível configurar a Rede Wi-Fi 2." >&2; exit 4; }
  if test -n "$pass"; then
    local key_mgmt=wpa-psk
    local scan
    scan="$(nm -t --escape no -f SSID,SECURITY device wifi list --rescan no ifname "$iface" 2>/dev/null || true)"
    if printf '%s\n' "$scan" | grep -Fxq -- "$ssid:WPA3"; then key_mgmt=sae; fi
    save_nm connection modify uuid "$candidate_uuid" 802-11-wireless-security.key-mgmt "$key_mgmt" 802-11-wireless-security.psk "$pass" ||
      { echo "A senha não foi aceita pelo perfil Wi-Fi. Verifique o tipo de segurança e a senha." >&2; exit 4; }
  fi
  if exists "$SECONDARY"; then
    save_nm connection modify "$SECONDARY" connection.id "$backup" ||
      { echo "Não foi possível preservar a segunda rede anterior." >&2; exit 5; }
  fi
  save_nm connection modify uuid "$candidate_uuid" connection.id "$SECONDARY" connection.autoconnect yes ||
    { echo "Não foi possível concluir o salvamento da Rede Wi-Fi 2." >&2; exit 5; }
  committed=1
  # An old backup can be the active profile. Do not disconnect it while saving.
  if test "$(active_name)" != "$backup"; then save_nm connection delete "$backup" || true; fi
  echo "Rede Wi-Fi 2 salva. A conexão ativa foi preservada."
)
