# Petição Brasil

**Plataforma de Democracia Participativa com Assinatura Digital Gov.br**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)

---

## 📋 Sobre o Projeto

O **Petição Brasil** é uma plataforma digital sem fins lucrativos que facilita o exercício da cidadania através de petições públicas com validade legal. Nossa missão é democratizar o acesso à participação política, permitindo que qualquer cidadão brasileiro possa criar, assinar e acompanhar petições de forma segura, transparente e legalmente válida.

### Principais Funcionalidades

- ✅ Criação de petições públicas com validação
- ✅ Assinatura digital através do Gov.br (ICP-Brasil)
- ✅ Verificação automática de assinaturas digitais
- ✅ **Certificado de Cadeia de Custódia** - Prova criptográfica de cada assinatura
- ✅ PDFs com hash criptográfico (SHA-256)
- ✅ Conformidade com LGPD (Lei Geral de Proteção de Dados)
- ✅ **Progressive Web App (PWA)** - Funciona offline, instalável em dispositivos
- ✅ Interface responsiva e acessível
- ✅ Sistema de moderação de conteúdo
- ✅ Transparência total das assinaturas
- ✅ Download em lote para criadores (PDFs + certificados)

---

## ⚠️ AVISOS IMPORTANTES - LEIA COM ATENÇÃO

### 1. Serviço Sem Fins Lucrativos

O **Petição Brasil** é uma plataforma **SEM FINS LUCRATIVOS** e **GRATUITA** dedicada à promoção da democracia participativa.

**NÃO NOS RESPONSABILIZAMOS POR:**
- ❌ Quaisquer perdas financeiras, diretas ou indiretas, decorrentes do uso da plataforma
- ❌ Custos com certificados digitais, internet, dispositivos ou equipamentos
- ❌ Despesas com assessoria jurídica, contábil ou administrativa
- ❌ Resultados ou efetividade de petições criadas
- ❌ Danos materiais, lucros cessantes ou custos de oportunidade

**A PLATAFORMA É FORNECIDA "NO ESTADO EM QUE SE ENCONTRA" (AS IS), SEM GARANTIAS DE QUALQUER TIPO.**

### 2. Limitação de Responsabilidade sobre Dados

Embora implementemos as melhores práticas de segurança da informação, **NÃO NOS RESPONSABILIZAMOS POR DIVULGAÇÃO DE DADOS** resultante de:

- 🔓 Dados intrinsecamente públicos (petições e assinaturas públicas)
- 🔓 Compartilhamento voluntário pelo usuário (redes sociais, etc.)
- 🔓 Violações em sistemas de terceiros (Gov.br, provedores de email, etc.)
- 🔓 Ataques cibernéticos sofisticados (hackers, ransomware, zero-day exploits)
- 🔓 Engenharia social (phishing, pretexting)
- 🔓 Dispositivos comprometidos (malware no dispositivo do usuário)
- 🔓 Ordens judiciais ou requisições de autoridades
- 🔓 Caso fortuito ou força maior (desastres naturais, guerras, etc.)

**NENHUM SISTEMA É 100% SEGURO. VOCÊ RECONHECE E ACEITA OS RISCOS INERENTES AO ARMAZENAMENTO E TRANSMISSÃO DE DADOS PELA INTERNET.**

### 3. Medidas de Segurança Implementadas

Apesar das limitações acima, implementamos:

- 🔒 Criptografia TLS/SSL em todas as transmissões
- 🔒 Armazenamento criptografado de dados sensíveis (CPF, senhas)
- 🔒 Sanitização automática de conteúdo (prevenção XSS)
- 🔒 Validação contra certificados ICP-Brasil
- 🔒 Backups criptografados e redundantes
- 🔒 Monitoramento de segurança contínuo
- 🔒 Controle de acesso baseado em menor privilégio
- 🔒 Conformidade com LGPD

### 4. Documentação Legal

Para informações completas sobre termos de uso e privacidade, consulte:

- 📄 [Termos de Uso](templates/static_pages/terms.html) - Seções 9 e 10
- 📄 [Política de Privacidade](templates/static_pages/privacy.html) - Seção 11
- 📄 [Sobre a Plataforma](templates/static_pages/about.html) - Aviso de responsabilidade

---

## � Certificado de Cadeia de Custódia

Cada assinatura verificada recebe automaticamente um **certificado oficial de cadeia de custódia** que comprova:

- ✅ **Autenticidade**: Assinatura verificada com certificado ICP-Brasil válido
- ✅ **Integridade**: Texto da petição não foi alterado após assinatura
- ✅ **Auditoria Completa**: Timeline cronológica de todo o processo
- ✅ **Não-Repúdio**: Hash SHA-256 impede negação ou adulteração
- ✅ **Valor Legal**: Evidência criptográfica juridicamente válida

**Conteúdo do Certificado:**
- Dados da verificação (timestamp, status, validações)
- Informações do certificado digital ICP-Brasil
- Hash SHA-256 das evidências de verificação
- Cadeia de custódia cronológica completa
- QR Code para verificação instantânea
- Hash do conteúdo da petição assinada

**Distribuição:**
- Signatários recebem certificado individual por email
- Criadores podem baixar pacote ZIP com todos PDFs + certificados
- Verificação pública via URL ou QR Code

---

## 🚀 Tecnologias Utilizadas

- **Backend:** Django 4.2+, Python 3.9+
- **Frontend:** TailwindCSS, Alpine.js
- **Banco de Dados:** PostgreSQL
- **Assinatura Digital:** Gov.br / ICP-Brasil
- **Armazenamento:** AWS S3
- **Task Queue:** Celery + Redis
- **Verificação PDF:** PyPDF2, cryptography
- **Geração PDF:** ReportLab, qrcode
- **Deploy:** Heroku / Railway

---

## 📦 Instalação e Desenvolvimento

### Pré-requisitos

- Python 3.9+
- PostgreSQL 12+
- Redis (para Celery)
- Conta AWS (para S3)

### Configuração Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/peticao-brasil.git
cd peticao-brasil

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Execute as migrações
python manage.py migrate

# Crie um superusuário
python manage.py createsuperuser

# Colete arquivos estáticos
python manage.py collectstatic

# Inicie o servidor de desenvolvimento
python manage.py runserver
```

### Variáveis de Ambiente Necessárias

```bash
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# AWS S3
AWS_ACCESS_KEY_ID=sua-access-key
AWS_SECRET_ACCESS_KEY=sua-secret-key
AWS_STORAGE_BUCKET_NAME=seu-bucket

# Email (SendGrid)
SENDGRID_API_KEY=sua-api-key
DEFAULT_FROM_EMAIL=noreply@peticaobrasil.com.br

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
```

---

## 🧪 Testes

Execute os testes com pytest:

```bash
# Todos os testes
pytest

# Testes específicos
pytest tests/test_views.py
pytest tests/test_security.py

# Com cobertura
pytest --cov=apps --cov-report=html
```

---

## 📚 Documentação

A documentação completa do projeto está em `/DOCS/`:

- [00-overview.md](DOCS/00-overview.md) - Visão geral do projeto
- [01-requirements-and-architecture.md](DOCS/01-requirements-and-architecture.md) - Requisitos e arquitetura
- [02-data-models.md](DOCS/02-data-models.md) - Modelos de dados
- [03-pdf-generation-and-signing.md](DOCS/03-pdf-generation-and-signing.md) - Geração e assinatura de PDFs
- [04-signature-verification.md](DOCS/04-signature-verification.md) - Verificação de assinaturas
- [05-user-interface-and-ux.md](DOCS/05-user-interface-and-ux.md) - Interface e UX
- [06-security-and-sanitization.md](DOCS/06-security-and-sanitization.md) - Segurança e sanitização
- [07-integration-testing.md](DOCS/07-integration-testing.md) - Testes de integração
- [08-deployment-checklist.md](DOCS/08-deployment-checklist.md) - Checklist de deploy
- [09-security-implementation.md](DOCS/09-security-implementation.md) - Implementação de segurança
- [10-next-steps.md](DOCS/10-next-steps.md) - Próximos passos
- [11-mobile-responsiveness.md](DOCS/11-mobile-responsiveness.md) - Responsividade mobile
- [12-custody-chain-certification.md](DOCS/12-custody-chain-certification.md) - Certificação de cadeia de custódia
- [13-pwa-implementation.md](DOCS/13-pwa-implementation.md) - **Implementação PWA** ⭐ NOVO

### 🚀 PWA (Progressive Web App)

O projeto agora é uma **Progressive Web App** completa! Veja [PWA_README.md](PWA_README.md) para início rápido.

**Recursos PWA:**
- 📱 Instalável em dispositivos móveis e desktop
- 🌐 Funciona offline com cache inteligente
- ⚡ Carregamento ultrarrápido
- 🔔 Suporte para notificações push
- 🔄 Atualizações automáticas

**Quick Start:**
```bash
# Gerar ícones
.\generate_pwa_icons.ps1

# Verificar configuração
python pwa_health_check.py

# Coletar arquivos estáticos
python manage.py collectstatic
```

---

## 🔐 Fundamentação Legal

A plataforma está em conformidade com:

- **Decreto nº 10.543/2020** - Assinatura eletrônica em documentos
- **MP 2.200-2/2001** - Infraestrutura de Chaves Públicas Brasileira (ICP-Brasil)
- **Lei nº 13.709/2018 (LGPD)** - Proteção de dados pessoais
- **Constituição Federal Art. 5º, XXXIV** - Direito de petição

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### Diretrizes de Contribuição

- Escreva testes para novas funcionalidades
- Mantenha o código limpo e documentado
- Siga as convenções PEP 8 para Python
- Atualize a documentação quando necessário

---

## 📄 Licença

Este projeto é open source e está licenciado sob a [Licença MIT](LICENSE).

---

## 📧 Contato

- **Email:** contato@peticaobrasil.com.br
- **Website:** [peticaobrasil.com.br](https://peticaobrasil.com.br)

---

## ⚖️ Disclaimer Final

**AO UTILIZAR ESTA PLATAFORMA, VOCÊ RECONHECE E ACEITA:**

1. Esta é uma plataforma **sem fins lucrativos** que não oferece garantias de resultados
2. Não nos responsabilizamos por **perdas financeiras** de qualquer natureza
3. Não nos responsabilizamos por **divulgação de dados** nas circunstâncias descritas acima
4. Nenhum sistema digital é 100% seguro, e você aceita os **riscos inerentes** ao uso da internet
5. Esta plataforma **não constitui assessoria jurídica, política ou administrativa**
6. Você leu e concorda com os [Termos de Uso](templates/static_pages/terms.html) e [Política de Privacidade](templates/static_pages/privacy.html)

**USE POR SUA CONTA E RISCO. A PLATAFORMA É FORNECIDA "AS IS" SEM GARANTIAS.**

---

**Última atualização:** Janeiro de 2026
