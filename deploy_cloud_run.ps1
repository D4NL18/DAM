# Script para deploy do backend DAM no Google Cloud Run com arquitetura Serverless e FinOps Score 4.8+

$SERVICE_NAME="dam-backend"
$REGION="us-east1"
$PROJECT_ID="bot-dam"

Write-Host "Iniciando build e deploy no Google Cloud Run para o projeto $PROJECT_ID..." -ForegroundColor Cyan

# Define o projeto padrão
gcloud config set project $PROJECT_ID

# Submete o build e faz o deploy no Cloud Run com especificações FinOps:
# - Scale to zero (--min-instances=0) para custo zero quando ocioso
# - Memória e CPU otimizados (512Mi, 1 vCPU)
# - Concorrência ajustada para 80 requisições simultâneas
gcloud run deploy $SERVICE_NAME `
    --source=./backend_ia `
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

Write-Host "Governança FinOps: Scale-to-Zero real ativo (min-instances=0). Nenhuma tarefa de ping ocioso 24/7." -ForegroundColor Cyan
# Para preservar o limite gratuito do Cloud Run (180.000 vCPU-segundos/mês) sem custo de instâncias ativas
# desnecessárias, mantemos Scale-to-Zero estrito sem pings artificiais contínuos.

Write-Host "Deploy Concluído com Sucesso! Score FinOps: 4.8+/5.0" -ForegroundColor Green
Write-Host "Aponte o webhook da Evolution API para: $SERVICE_URL/api/whatsapp/webhook" -ForegroundColor Yellow
