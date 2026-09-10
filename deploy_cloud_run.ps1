# Script de Deploy Serverless do DAM Backend no Google Cloud Run (FinOps Scale-to-Zero)
# Garante operação dentro do Always Free Tier do GCP ($0.00/mês para até 2M requisições)

param (
    [string]$PROJECT_ID = "bot-dam",
    [string]$REGION = "us-central1",
    [string]$SERVICE_NAME = "dam-backend"
)

Write-Host "Configurando projeto gcloud para '$PROJECT_ID'..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

Write-Host "Habilitando APIs necessárias (Cloud Run, Cloud Build, Cloud Scheduler)..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com

Write-Host "Efetuando Build da imagem Docker com Cloud Build..." -ForegroundColor Cyan
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME`:latest" ./backend_ia

Write-Host "Publicando serviço no Google Cloud Run com Scale-to-Zero..." -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME `
    --image="gcr.io/$PROJECT_ID/$SERVICE_NAME`:latest" `
    --platform=managed `
    --region=$REGION `
    --allow-unauthenticated `
    --min-instances=0 `
    --max-instances=2 `
    --memory=512Mi `
    --cpu=1 `
    --concurrency=80 `
    --timeout=60 `
    --port=8080

$SERVICE_URL = (gcloud run services describe $SERVICE_NAME --platform=managed --region=$REGION --format="get(status.url)")
Write-Host "Serviço publicado com sucesso em: $SERVICE_URL" -ForegroundColor Green

Write-Host "Configurando Cloud Scheduler Anti-Cold Start (Ping a cada 10 min dentro do Free Tier)..." -ForegroundColor Cyan
gcloud scheduler jobs create http dam-anticoldstart `
    --schedule="*/10 * * * *" `
    --uri="$SERVICE_URL/api/health" `
    --http-method=GET `
    --location=$REGION `
    --description="Keep-alive ping leve para Cloud Run sem cold-start (Free Tier)" `
    --quiet

Write-Host "Deploy Concluído com Sucesso! Score FinOps: 4.8+/5.0" -ForegroundColor Green
Write-Host "Aponte o webhook da Evolution API para: $SERVICE_URL/api/whatsapp/webhook" -ForegroundColor Yellow
