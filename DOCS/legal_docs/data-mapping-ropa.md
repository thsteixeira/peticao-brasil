# Registro de Atividades de Tratamento de Dados (ROPA)
**Petição Brasil - Lei Geral de Proteção de Dados**

**Tipo de Documento:** Conformidade Legal (LGPD Art. 37)  
**Criado em:** 25 de janeiro de 2026  
**Última Atualização:** 25 de janeiro de 2026  
**Frequência de Revisão:** Trimestral  
**Responsável:** Encarregado (contato@peticaobrasil.com.br)

---

## Finalidade do Documento

Este Registro de Atividades de Tratamento de Dados (ROPA) documenta todas as operações de tratamento de dados pessoais realizadas pela Petição Brasil, conforme exigido pelo Artigo 37 da Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018).

**Exigência Legal:** LGPD Art. 37 determina que os controladores mantenham registro das operações de tratamento de dados pessoais sob sua responsabilidade.

---

## 1. Identificação do Controlador

| Campo | Informação |
|-------|------------|
| **Nome da Organização** | Petição Brasil |
| **Natureza Jurídica** | Plataforma Digital para Participação Democrática |
| **Atividade Principal** | Gestão de petições online com assinaturas digitais |
| **Encarregado de Dados** | Petição Brasil (designação interna) |
| **Contato do Encarregado** | contato@peticaobrasil.com.br |
| **Jurisdição** | Brasil |
| **Legislação Aplicável** | LGPD (Lei 13.709/2018), Marco Civil da Internet (Lei 12.965/2014) |

---

## 2. Categorias de Dados Pessoais Tratados

### 2.1 Dados de Conta de Usuário

**Atividade de Tratamento:** Cadastro e autenticação de usuários  
**Base Legal:** Consentimento (LGPD Art. 7, I)  
**Controlador:** Petição Brasil  
**Operadores:** Heroku (hospedagem), AWS (backups)

| Nome do Campo | Tipo de Dado | Sensibilidade | Finalidade | Período de Retenção | Criptografia |
|---------------|--------------|---------------|------------|---------------------|--------------|
| `username` | Pessoal | Baixa | Autenticação na plataforma | Enquanto ativo + 5 anos | Não |
| `first_name` | Pessoal | Baixa | Identificação do usuário | Enquanto ativo + 5 anos | Não |
| `last_name` | Pessoal | Baixa | Identificação do usuário | Enquanto ativo + 5 anos | Não |
| `email` | Pessoal | Baixa | Comunicação, autenticação | Enquanto ativo + 5 anos | Não |
| `password` | Sensível | Alta | Autenticação | Enquanto ativo + 5 anos | Sim (bcrypt) |
| `date_joined` | Não pessoal | N/A | Trilha de auditoria | Indefinido | Não |
| `last_login` | Não pessoal | N/A | Monitoramento de segurança | Indefinido | Não |
| `is_active` | Não pessoal | N/A | Controle de acesso | Indefinido | Não |
| `is_staff` | Não pessoal | N/A | Controle de acesso | Indefinido | Não |

**Titulares dos Dados:** Usuários cadastrados (18+ anos)  
**Volume de Dados:** Contas de usuários ativos  
**Método de Coleta:** Entrada direta via formulários web  
**Local de Armazenamento:** Banco de dados PostgreSQL no Heroku (EUA), backups AWS (EUA/Brasil)  
**Controles de Acesso:** Painel administrativo protegido por senha, permissões baseadas em função  
**Processo de Exclusão:** Manual mediante solicitação do usuário ou automatizado após 5 anos de inatividade

---

### 2.2 Dados de Petições

**Atividade de Tratamento:** Criação e gestão de petições públicas  
**Base Legal:** Legítimo interesse (LGPD Art. 7, IX - Participação democrática)  
**Controlador:** Petição Brasil  
**Operadores:** Heroku (hospedagem), Cloudflare (CDN)

| Nome do Campo | Tipo de Dado | Sensibilidade | Finalidade | Período de Retenção | Criptografia |
|---------------|--------------|---------------|------------|---------------------|--------------|
| `title` | Não pessoal | N/A | Informação pública | Enquanto ativa + 5 anos | Não |
| `description` | Não pessoal | N/A | Informação pública | Enquanto ativa + 5 anos | Não |
| `creator` (FK) | Pessoal | Baixa | Atribuição | Enquanto ativa + 5 anos | Não |
| `category` | Não pessoal | N/A | Organização | Enquanto ativa + 5 anos | Não |
| `signature_goal` | Não pessoal | N/A | Funcionalidade da plataforma | Enquanto ativa + 5 anos | Não |
| `status` | Não pessoal | N/A | Gestão de fluxo de trabalho | Enquanto ativa + 5 anos | Não |
| `slug` | Não pessoal | N/A | Roteamento de URL | Enquanto ativa + 5 anos | Não |
| `image` | Não pessoal | N/A | Apresentação visual | Enquanto ativa + 5 anos | Não |

**Titulares dos Dados:** Criadores de petições (usuários cadastrados)  
**Compartilhamento de Dados:** Acessível publicamente na internet  
**Transferência Internacional:** Sim (cache de CDN globalmente via Cloudflare)  
**Método de Coleta:** Entrada direta via formulário de criação de petição  
**Local de Armazenamento:** Banco de dados PostgreSQL, S3 (imagens)  
**Controles de Acesso:** Leitura pública, escrita autenticada (apenas criador)

---

### 2.3 Dados de Assinaturas (Mais Sensíveis)

**Atividade de Tratamento:** Coleta e verificação de assinaturas digitais  
**Base Legal:** Obrigação legal (LGPD Art. 7, II - Conformidade com regulamentos ICP-Brasil)  
**Controlador:** Petição Brasil  
**Operadores:** Heroku (hospedagem), AWS S3 (armazenamento de PDF), Gov.br (validação de assinatura)

| Nome do Campo | Tipo de Dado | Sensibilidade | Finalidade | Período de Retenção | Criptografia |
|---------------|--------------|---------------|------------|---------------------|--------------|
| `full_name` | Pessoal | Média | Participação democrática | 10 anos | Não |
| `cpf_hash` | Sensível | Alta | Prevenção de duplicatas, verificação | 10 anos | Sim (SHA-256) |
| `email` | Pessoal | Média | Confirmação, atualizações | 10 anos | Não |
| `city` | Pessoal | Baixa | Estatísticas geográficas | 10 anos | Não |
| `state` | Pessoal | Baixa | Estatísticas geográficas | 10 anos | Não |
| `signed_pdf` | Sensível | Alta | Evidência legal | 10 anos | Sim (criptografia S3 em repouso) |
| `certificate_info` | Sensível | Média | Validação de assinatura digital | 10 anos | Não (JSON estruturado) |
| `verification_status` | Não pessoal | N/A | Controle de qualidade | 10 anos | Não |
| `rejection_reason` | Não pessoal | N/A | Trilha de auditoria | 90 dias (rejeitadas) | Não |
| `ip_address_hash` | Pessoal | Média | Prevenção de fraudes, auditoria | 6 meses | Sim (SHA-256) |
| `user_agent` | Pessoal | Baixa | Detecção de fraudes | 6 meses | Não |
| `created_at` | Não pessoal | N/A | Rastreamento temporal | 10 anos | Não |

**Exigência Legal de Retenção:** 10 anos (Código Civil Art. 205 - prazo prescricional para documentos legais)  
**Categoria Especial:** Assinaturas digitais têm valor legal equivalente a assinaturas manuscritas (Decreto 10.543/2020)  
**Titulares dos Dados:** Signatários de petições (autenticados via Gov.br)  
**Volume de Dados:** Todas as assinaturas (aprovadas, pendentes, rejeitadas)  
**Método de Coleta:** Upload e validação de assinatura digital Gov.br  
**Local de Armazenamento:** PostgreSQL (metadados), AWS S3 (arquivos PDF)  
**Controles de Acesso:** Criptografado em repouso, acesso apenas autenticado  
**Processo de Exclusão:** Não pode ser totalmente excluído antes de 10 anos; dados pessoais anonimizados mediante solicitação do usuário (nome → "[Usuário Removido]", hash CPF limpo)

**Regras de Anonimização:**
- Assinaturas rejeitadas: Automaticamente anonimizadas após 90 dias
- Solicitações de exclusão de usuário: Dados pessoais anonimizados mas registro de assinatura mantido para conformidade legal
- Após 10 anos: Exclusão completa permitida

---

### 2.4 Logs de Auditoria e Segurança

**Atividade de Tratamento:** Moderação da plataforma e monitoramento de segurança  
**Base Legal:** Obrigação legal (LGPD Art. 7, II + Marco Civil da Internet Art. 15)  
**Controlador:** Petição Brasil

| Nome do Campo | Tipo de Dado | Sensibilidade | Finalidade | Período de Retenção | Criptografia |
|---------------|--------------|---------------|------------|---------------------|--------------|
| `moderator` (FK) | Pessoal | Baixa | Responsabilização | 5 anos | Não |
| `action_type` | Não pessoal | N/A | Trilha de auditoria | 5 anos | Não |
| `content_type` | Não pessoal | N/A | Rastreamento de objeto | 5 anos | Não |
| `object_id` | Não pessoal | N/A | Rastreamento de objeto | 5 anos | Não |
| `reason` | Não pessoal | N/A | Justificativa | 5 anos | Não |
| `ip_address` | Pessoal | Média | Segurança, conformidade | 6 meses | Não |
| `created_at` | Não pessoal | N/A | Rastreamento temporal | 5 anos | Não |

**Exigência Legal:** Marco Civil da Internet (Lei 12.965/2014) Art. 15 exige retenção mínima de 6 meses de logs de acesso  
**Titulares dos Dados:** Moderadores da plataforma, conteúdo sendo moderado  
**Método de Coleta:** Registro automático via sinais Django  
**Local de Armazenamento:** Banco de dados PostgreSQL  
**Controles de Acesso:** Acesso somente para administradores  
**Processo de Exclusão:** Endereços IP automaticamente limpos após 6 meses

---

## 3. Operadores de Dados Terceirizados

| Operador | Tipo de Serviço | Dados Processados | Localização | Status DPA | Última Revisão |
|----------|-----------------|-------------------|-------------|------------|----------------|
| **Heroku (Salesforce)** | Hospedagem de aplicação | Todos os dados da aplicação (banco de dados, sessões) | EUA | ✅ DPA Padrão | Jan 2026 |
| **AWS S3** | Armazenamento de arquivos | PDFs assinados, imagens de petições, arquivos estáticos | EUA/Brasil | ✅ DPA Padrão | Jan 2026 |
| **Cloudflare** | CDN, proteção DDoS | Logs de acesso, conteúdo público em cache | Global | ✅ DPA Padrão | Jan 2026 |
| **Gov.br (Serpro)** | Validação de assinatura digital | Solicitações de validação de certificado | Brasil | ✅ Governo | N/A |

**Salvaguardas de Transferência Internacional:**
- AWS: Cláusulas Contratuais Padrão (SCCs), DPA compatível com GDPR
- Heroku: Adendo de Processamento de Dados da Salesforce com SCCs
- Cloudflare: DPA padrão com provisões de transferência internacional
- Gov.br: Sem transferência (serviço do governo brasileiro)

**Cronograma de Revisão de DPA:** Revisão anual de todos os Acordos de Processamento de Dados  
**Armazenamento de DPA:** `/DOCS/legal_docs/processor-agreements/`

---

## 4. Diagramas de Fluxo de Dados

### 4.1 Fluxo de Cadastro de Usuário

```
Navegador do Usuário → HTTPS → Aplicação Django (Heroku) → PostgreSQL (Heroku)
                                         ↓
                                Senha com hash (bcrypt)
                                         ↓
                                Armazenada criptografada
```

### 4.2 Fluxo de Assinatura Digital

```
Usuário → Autenticação Gov.br → Upload de PDF Assinado
                                         ↓
                                 Aplicação Django
                                         ↓
                        ┌────────────────┴───────────────────┐
                        ↓                                    ↓
                Extração de CPF                    Armazenamento PDF (S3)
                        ↓                                    ↓
                Hash (SHA-256)                     Criptografado em repouso
                        ↓                                    ↓
                PostgreSQL (metadados)              Bucket S3 (arquivos)
```

### 4.3 Fluxo de Exclusão de Dados (Solicitação do Usuário)

```
Solicitação por Email → Revisão do Encarregado → Verificação
                                   ↓
                    ┌──────────────┴───────────────┐
                    ↓                              ↓
            Conta de Usuário                   Assinaturas
                    ↓                              ↓
        Pode excluir (se sem petições)      Anonimizar dados
                    ↓                              ↓
            Removido do BD                Manter registro (exigência legal)
                                                   ↓
                                        Nome → "[Removido]"
                                        CPF → NULL
                                        Email → "anonimizado@lgpd.local"
```

---

## 5. Cronograma de Retenção de Dados

| Categoria de Dados | Retenção Ativa | Retenção Pós-Exclusão | Base Legal | Anonimização |
|--------------------|----------------|-----------------------|------------|--------------|
| Contas de usuário | Enquanto ativo | 5 anos após último login | Legítimo interesse | Após 5 anos de inatividade |
| Senhas de usuário | Enquanto ativo | Excluída com a conta | Consentimento | Imediata |
| Dados de petição | Enquanto ativa | 5 anos após encerramento | Legítimo interesse | Não aplicável (público) |
| Assinaturas aprovadas | N/A | 10 anos | Obrigação legal (Código Civil 205) | Não pode anonimizar antes de 10 anos |
| Assinaturas rejeitadas | 90 dias | Anonimizada | Minimização de dados | Após 90 dias |
| Endereços IP (assinaturas) | 6 meses | Excluído | Marco Civil Art. 15 | Após 6 meses |
| Endereços IP (logs) | 6 meses | Excluído | Marco Civil Art. 15 | Após 6 meses |
| Logs de moderação | 5 anos | Mantido | Responsabilização | IP limpo após 6 meses |
| Dados de sessão | 2 semanas | Excluído | Necessidade técnica | Imediata |

**Tarefas de Limpeza Automatizada:**
- Assinaturas rejeitadas → Anonimizadas após 90 dias (tarefa Celery - semanal)
- Endereços IP → Limpos após 6 meses (tarefa Celery - mensal)
- Contas inativas → Anonimizadas após 5 anos (tarefa Celery - mensal)

---

## 6. Matriz de Controle de Acesso

| Papel | Dados de Usuário | Dados de Petição | Dados de Assinatura | Logs de Auditoria | Painel Admin |
|-------|------------------|------------------|---------------------|-------------------|--------------|
| **Anônimo** | - | Leitura (público) | - | - | - |
| **Usuário Cadastrado** | Apenas próprio | Ler todos, Criar | Ver próprias | - | - |
| **Criador de Petição** | Apenas próprio | Ler todos, Editar próprias | Ver para próprias petições | - | - |
| **Moderador** | Leitura | Ler todos, Editar status | Ler, Verificar | Leitura | Limitado |
| **Administrador** | Completo | Completo | Completo | Completo | Completo |
| **Encarregado** | Leitura (para solicitações) | Leitura | Leitura | Leitura | Limitado |

**Método de Autenticação:** Autenticação baseada em sessão Django  
**Política de Senhas:** Mínimo 8 caracteres, requisitos de complexidade aplicados  
**Acesso Admin:** MFA recomendado (a ser implementado)  
**Trilha de Auditoria:** Todas as ações de admin registradas em ModerationLog

---

## 7. Medidas de Segurança

### 7.1 Criptografia

| Tipo de Dado | Método de Criptografia | Gestão de Chaves |
|--------------|------------------------|------------------|
| Senhas | bcrypt (fator de trabalho 12) | Django secrets |
| CPF | Hash SHA-256 | Unidirecional (irreversível) |
| Endereços IP | Hash SHA-256 | Unidirecional (irreversível) |
| Dados em trânsito | TLS 1.2+ (HTTPS) | Certificados Let's Encrypt |
| Dados em repouso (S3) | AES-256 | Chaves gerenciadas AWS |
| Conexões de banco de dados | SSL/TLS | PostgreSQL SSL obrigatório |

### 7.2 Salvaguardas Técnicas

- Cabeçalhos Content Security Policy (CSP)
- Proteção CSRF (middleware Django)
- Prevenção XSS (escape de template Django)
- Prevenção de injeção SQL (Django ORM)
- Limitação de taxa em endpoints de autenticação
- Cookies de sessão seguros (HTTPOnly, Secure, SameSite)
- Validação e sanitização de entrada
- Restrições de upload de arquivo (somente PDF, limites de tamanho)

### 7.3 Medidas Organizacionais

- Controle de acesso baseado em função (RBAC)
- Registro de auditoria de todas as modificações de dados
- Atualizações e patches de segurança regulares
- Plano de resposta a incidentes documentado
- Encarregado designado e treinado
- Acordos de Processamento de Dados com todos os operadores
- Revisões anuais de segurança

---

## 8. Cumprimento dos Direitos dos Titulares

**Método de Contato:** Email para contato@peticaobrasil.com.br  
**SLA de Resposta:** 15 dias corridos  
**Processo de Verificação:** Confirmação por email ou validação de CPF

| Direito (Artigo LGPD) | Método de Implementação | Tempo Estimado de Processamento |
|-----------------------|------------------------|----------------------------------|
| Acesso (Art. 18, II) | Exportação manual de dados para JSON | 5-10 dias |
| Correção (Art. 18, III) | Atualização manual do banco de dados | 3-5 dias |
| Exclusão (Art. 18, VI) | Anonimização manual (assinaturas mantidas) | 5-10 dias |
| Portabilidade (Art. 18, V) | Exportação JSON via email | 5-10 dias |
| Informação (Art. 18, I) | Referência à Política de Privacidade + ROPA | 1-3 dias |
| Revogação (Art. 8, §5º) | Processamento manual | 3-5 dias |
| Oposição (Art. 18, §2º) | Revisão e processamento manual | 5-10 dias |

**Limitações:**
- Assinaturas não podem ser totalmente excluídas antes do período legal de retenção de 10 anos
- Dados públicos de petição não podem ser removidos (legítimo interesse em transparência)
- Logs de auditoria mantidos para responsabilização (5 anos)

---

## 9. Contatos para Resposta a Incidentes

| Papel | Nome/Departamento | Email | Telefone | Responsabilidade |
|-------|-------------------|-------|----------|------------------|
| **Encarregado** | Petição Brasil | contato@peticaobrasil.com.br | - | Contato primário, ligação ANPD |
| **Líder Técnico** | Administrador do Sistema | contato@peticaobrasil.com.br | - | Contenção de violação |
| **Assessoria Jurídica** | Consultor Externo | A definir | - | Revisão de conformidade legal |
| **ANPD** | Autoridade Governamental | - | - | Destinatário de notificação de violação |

**Plano de Resposta a Incidentes:** Ver `/DOCS/legal_docs/incident-response-plan.md`  
**Prazo de Notificação de Violação:** 72 horas para ANPD (se necessário)

---

## 10. Status de Avaliação de Impacto à Proteção de Dados (DPIA)

**DPIA Necessária:** Não (atividades atuais de processamento não são de alto risco)  
**Justificativa:**
- Sem processamento em larga escala de dados sensíveis
- Sem monitoramento sistemático
- Sem tomada de decisão automatizada
- Bases legais claras para todo processamento
- Fortes salvaguardas técnicas implementadas

**Gatilho de Revisão:** Qualquer nova atividade de processamento de alto risco (ex: perfilamento automatizado, coleta de dados biométricos)

---

## 11. Transferências Internacionais de Dados

| País de Destino | Dados Transferidos | Mecanismo Legal | Operador |
|-----------------|-------------------|-----------------|----------|
| Estados Unidos | Todos os dados da aplicação | Cláusulas Contratuais Padrão | Heroku, AWS |
| Estados Unidos | Hospedagem de arquivos estáticos | Cláusulas Contratuais Padrão | AWS S3 |
| Global (CDN) | Dados públicos de petição, conteúdo em cache | Cláusulas Contratuais Padrão | Cloudflare |

**Salvaguardas de Transferência:**
- Todos os operadores têm DPAs compatíveis com GDPR (aplicável à LGPD)
- Dados criptografados em trânsito (TLS) e em repouso (AES-256)
- Compromissos contratuais com padrões brasileiros de proteção de dados
- Direito de auditar medidas de segurança do operador

---

## 12. Registro de Alterações

| Data | Versão | Alterações | Atualizado Por |
|------|--------|------------|----------------|
| 25/01/2026 | 1.0 | Criação inicial do ROPA | Encarregado |

---

## 13. Cronograma de Revisão

**Revisões Trimestrais:** Março, Junho, Setembro, Dezembro  
**Gatilhos para Revisão Fora do Ciclo:**
- Novas atividades de tratamento de dados
- Mudanças nos requisitos legais
- Violações de dados ou incidentes
- Novos operadores terceirizados
- Mudanças significativas no sistema

**Próxima Revisão Programada:** Abril de 2026

---

## 14. Declaração de Conformidade

Este Registro de Atividades de Tratamento de Dados (ROPA) foi preparado de acordo com o Artigo 37 da Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018). Reflete com precisão todas as operações de tratamento de dados pessoais conduzidas pela Petição Brasil em 25 de janeiro de 2026.

**Preparado por:** Encarregado - Petição Brasil  
**Contato:** contato@peticaobrasil.com.br  
**Data:** 25 de janeiro de 2026

---

**Status do Documento:** Ativo  
**Classificação:** Interno - Conformidade Legal  
**Local de Armazenamento:** `/DOCS/legal_docs/data-mapping-ropa.md`
