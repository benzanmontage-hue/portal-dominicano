#!/usr/bin/env bash
# Ciclo de actualización: descarga datos, regenera páginas, publica (git + Cloudflare) y difunde.
# Uso: scripts/ciclo.sh VUELTAS MINUTOS
#   VUELTAS  cuántas actualizaciones hacer en esta ejecución (1 = una sola)
#   MINUTOS  espera entre vueltas
# GitHub solo arranca las tareas programadas unas pocas veces al día, así que cada ejecución
# se queda activa varias horas y actualiza cada MINUTOS minutos. Entre la 1 y las 7 AM (hora RD)
# no hay sorteos: esas vueltas se saltan.
set -u
VUELTAS=${1:-1}
MINUTOS=${2:-20}
PROYECTO=${CF_PAGES_PROJECT:-portal-dominicano}
FALLOS=0

git config user.name "portal-bot"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

publicar_cloudflare() {
  [ -z "${CLOUDFLARE_API_TOKEN:-}" ] && return 0
  rm -rf _site && mkdir -p _site
  rsync -a --exclude '.git' --exclude '.github' --exclude '_site' --exclude 'scripts' \
    --exclude 'screenshots' --exclude 'README.md' --exclude 'LICENSE' --exclude '.gitignore' \
    --exclude 'data/sitemap_estado.json' --exclude 'data/tarjeta*.txt' ./ _site/
  npx -y wrangler@3 pages deploy _site --project-name="$PROYECTO" --branch=main --commit-dirty=true >/dev/null 2>&1 \
    && echo "  Cloudflare: publicado" || { echo "::warning::No se pudo publicar en Cloudflare"; return 1; }
}

difundir() {  # solo cuando cambian los números
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    curl -sS -F chat_id="${TELEGRAM_CHAT_ID:-}" -F photo=@compartir/resultados-hoy.png \
      -F caption="$(head -c 1000 data/tarjeta.txt)" -F parse_mode=Markdown \
      "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendPhoto" | grep -q '"ok":true' && echo "  Telegram: enviado"
  fi
  if [ -n "${FB_PAGE_TOKEN:-}" ]; then
    H=$(TZ=America/Santo_Domingo date +%H)
    case "$H" in 13|19|21)
      curl -sS -F source=@compartir/resultados-hoy.png -F message="$(cat data/tarjeta.txt)" \
        -F access_token="$FB_PAGE_TOKEN" "https://graph.facebook.com/v21.0/${FB_PAGE_ID:-}/photos" | grep -q '"id"' && echo "  Facebook: publicado";;
    esac
  fi
}

una_vuelta() {
  # Partir siempre de lo último publicado (otra ejecución pudo publicar entretanto).
  git fetch -q origin main && git reset -q --hard origin/main
  python3 scripts/update_all.py || FALLOS=$((FALLOS + 1))
  git add -A
  if git diff --cached --quiet; then
    echo "  Sin cambios"
    return 0
  fi
  NUMEROS=no
  git diff --cached --quiet -- data/tarjeta_numeros.txt || NUMEROS=si
  git commit -q -m "auto-update datos ($(TZ=America/Santo_Domingo date '+%d/%m/%Y %H:%M') RD)"
  git push -q origin HEAD:main || return 2   # alguien publicó antes: repetir la vuelta
  publicar_cloudflare
  python3 scripts/indexnow.py || true
  [ "$NUMEROS" = si ] && difundir
  return 0
}

for i in $(seq 1 "$VUELTAS"); do
  H=$(TZ=America/Santo_Domingo date +%-H)
  if [ "$VUELTAS" -gt 1 ] && [ "$H" -ge 1 ] && [ "$H" -lt 7 ]; then
    echo "Vuelta $i: $(TZ=America/Santo_Domingo date '+%H:%M') RD, de madrugada; se salta"
  else
    echo "Vuelta $i: $(TZ=America/Santo_Domingo date '+%H:%M') RD"
    una_vuelta || { echo "  reintento"; sleep 5; una_vuelta || true; }
  fi
  [ "$i" -lt "$VUELTAS" ] && sleep $((MINUTOS * 60))
done

if [ "$FALLOS" -gt 0 ]; then
  echo "::warning::$FALLOS vuelta(s) con fallos en la descarga de datos o en la generación de páginas"
fi
exit 0
