# Script de Deploy Automático no GCP (Projeto: bom-dam)
# Execute este arquivo APÓS preencher o .env e o firebase-adminsdk.json na pasta backend_ia

$PROJECT_ID = "bot-dam"
$ZONE = "us-central1-a"
$VM_NAME = "dam-server"

Write-Host "Configurando projeto gcloud..."
gcloud config set project $PROJECT_ID

Write-Host "Habilitando Compute Engine API (pode demorar um pouco se for a primeira vez)..."
gcloud services enable compute.googleapis.com

Write-Host "Criando regras de firewall para as portas 8000 (FastAPI) e 8080 (Evolution Go)..."
gcloud compute firewall-rules create allow-dam-ports `
    --allow "tcp:8000,tcp:8080" `
    --target-tags dam-server `
    --description "Allow incoming traffic on 8000 and 8080"

Write-Host "Criando a Máquina Virtual (e2-micro)..."
gcloud compute instances create $VM_NAME `
    --project=$PROJECT_ID `
    --zone=$ZONE `
    --machine-type=e2-micro `
    --tags=dam-server `
    --metadata-from-file=startup-script=startup.sh

Write-Host "Aguardando 60 segundos para a máquina inicializar e instalar o Docker..."
Start-Sleep -Seconds 60

Write-Host "Enviando os arquivos do projeto para a VM..."
gcloud compute scp --recurse .\backend_ia .\docker-compose.yml $VM_NAME`:~/ --zone=$ZONE

Write-Host "Iniciando os containers na nuvem!"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="sudo docker-compose up -d --build"

Write-Host "Deploy Concluído!"
$IP = (gcloud compute instances describe $VM_NAME --zone=$ZONE --format="get(networkInterfaces[0].accessConfigs[0].natIP)")
Write-Host "Sua Evolution Go está rodando em: http://$IP:8080"
Write-Host "Seu Motor de IA está rodando em: http://$IP:8000"
Write-Host "LEMBRE-SE: No Evolution Go, configure o Webhook para apontar para: http://backend_ia:8000/api/whatsapp/webhook"
