# Plano de Resposta a Incidentes de Segurança de Dados
**Petição Brasil - Lei Geral de Proteção de Dados**

**Tipo de Documento:** Conformidade Legal (LGPD Art. 48)  
**Criado em:** 25 de janeiro de 2026  
**Última Atualização:** 25 de janeiro de 2026  
**Frequência de Revisão:** Semestral  
**Responsável:** Encarregado de Dados (contato@peticaobrasil.com.br)

---

## Finalidade do Documento

Este Plano de Resposta a Incidentes estabelece procedimentos para detectar, responder e notificar incidentes de segurança envolvendo dados pessoais, conforme exigido pelo Artigo 48 da LGPD.

**Base Legal:**
> **LGPD Art. 48.** O controlador deverá comunicar à autoridade nacional e ao titular a ocorrência de incidente de segurança que possa acarretar risco ou dano relevante aos titulares.
> 
> **§ 1º** A comunicação será feita em prazo razoável, conforme definido pela autoridade nacional, e deverá mencionar, no mínimo:
> 
> I - a descrição da natureza dos dados pessoais afetados;
> 
> II - as informações sobre os titulares envolvidos;
> 
> III - a indicação das medidas técnicas e de segurança utilizadas para a proteção dos dados, observados os segredos comercial e industrial;
> 
> IV - os riscos relacionados ao incidente;
> 
> V - os motivos da demora, no caso de a comunicação não ter sido imediata; e
> 
> VI - as medidas que foram ou que serão adotadas para reverter ou mitigar os efeitos do prejuízo.

---

## 1. Definições

### 1.1 O que Constitui um Incidente de Dados?

**Incidente de Segurança de Dados:** Qualquer evento que comprometa a confidencialidade, integridade ou disponibilidade de dados pessoais.

**Exemplos de Incidentes:**

| Tipo | Descrição | Exemplos Específicos |
|------|-----------|---------------------|
| **Acesso Não Autorizado** | Indivíduo ou sistema não autorizado acessa dados pessoais | - Invasão de banco de dados<br>- Credenciais de admin roubadas<br>- Bypass de autenticação |
| **Divulgação Não Autorizada** | Dados pessoais expostos a partes não autorizadas | - Configuração incorreta de S3 (bucket público)<br>- Email enviado para destinatário errado<br>- Publicação acidental de logs com dados |
| **Perda de Dados** | Dados pessoais perdidos e irrecuperáveis | - Falha de backup<br>- Exclusão acidental de registros<br>- Corrupção de banco de dados |
| **Modificação Não Autorizada** | Dados pessoais alterados sem autorização | - Ataque de injeção SQL<br>- Manipulação de formulários<br>- Adulteração de assinaturas |
| **Indisponibilidade** | Dados pessoais inacessíveis quando necessários | - Ataque DDoS<br>- Falha de servidor<br>- Ransomware |
| **Phishing/Engenharia Social** | Tentativa de obter acesso através de engano | - Emails de phishing para usuários<br>- Tentativas de redefinição de senha fraudulentas |

### 1.2 O que NÃO é um Incidente?

- Solicitações legítimas de acesso a dados por titulares
- Manutenção planejada do sistema (com notificação)
- Tentativas bloqueadas de acesso (sem sucesso)
- Atualizações legítimas de dados por usuários autorizados

---

## 2. Classificação de Severidade

### 2.1 Níveis de Severidade

| Nível | Nome | Critérios | Prazo de Resposta | Notificação ANPD? | Notificação Titular? |
|-------|------|-----------|-------------------|-------------------|----------------------|
| **1** | Crítico | - Dados sensíveis expostos<br>- Grande número de titulares (>1.000)<br>- Alto risco de dano | Imediata (0-2h) | Sim (72h) | Sim (72h) |
| **2** | Alto | - Dados pessoais expostos<br>- Número moderado de titulares (100-1.000)<br>- Risco moderado de dano | Urgente (2-6h) | Avaliação caso a caso | Avaliação caso a caso |
| **3** | Médio | - Exposição limitada<br>- Pequeno número de titulares (<100)<br>- Risco baixo de dano | Prioritário (6-24h) | Provavelmente não | Provavelmente não |
| **4** | Baixo | - Tentativa bloqueada<br>- Nenhum titular afetado<br>- Sem risco de dano | Normal (24-48h) | Não | Não |

### 2.2 Fatores de Avaliação de Risco

**Considerar ao avaliar severidade:**
1. **Tipo de Dados Afetados:**
   - Dados sensíveis (CPF hash, PDFs assinados) = maior risco
   - Dados públicos (títulos de petições) = menor risco

2. **Quantidade de Titulares:**
   - >1.000 titulares = alto risco
   - 100-1.000 titulares = médio risco
   - <100 titulares = baixo risco

3. **Probabilidade de Dano:**
   - Risco de fraude/roubo de identidade = alto
   - Risco de spam/incômodo = médio
   - Sem risco identificável = baixo

4. **Duração da Exposição:**
   - >30 dias = alto risco
   - 1-30 dias = médio risco
   - <24 horas = baixo risco

5. **Facilidade de Identificação:**
   - Dados permitem identificação direta (nome + CPF) = alto risco
   - Dados semi-identificáveis (apenas email) = médio risco
   - Dados anonimizados/agregados = baixo risco

---

## 3. Equipe de Resposta a Incidentes

### 3.1 Papéis e Responsabilidades

| Papel | Responsável | Contato | Responsabilidades |
|-------|-------------|---------|-------------------|
| **Coordenador de Incidente** | Encarregado de Dados | contato@peticaobrasil.com.br | - Liderar resposta<br>- Coordenar comunicações<br>- Decidir sobre notificações<br>- Documentar incidente |
| **Líder Técnico** | Administrador do Sistema | contato@peticaobrasil.com.br | - Investigar tecnicamente<br>- Implementar contenção<br>- Restaurar sistemas<br>- Coletar evidências |
| **Assessoria Jurídica** | Consultor Externo | [A contratar quando necessário] | - Avaliar obrigações legais<br>- Revisar comunicações<br>- Aconselhar sobre notificações |
| **Comunicação** | Administração | contato@peticaobrasil.com.br | - Redigir notificações<br>- Comunicar com titulares<br>- Gerenciar relações públicas |

### 3.2 Autoridades Externas

| Autoridade | Quando Contactar | Como Contactar |
|------------|------------------|----------------|
| **ANPD** (Autoridade Nacional de Proteção de Dados) | Incidentes de Nível 1 (Crítico)<br>Alguns incidentes de Nível 2 | - Portal: www.gov.br/anpd<br>- Email: [conforme portal ANPD]<br>- Prazo: 72 horas |
| **Polícia Federal** | Crimes cibernéticos (invasão, roubo de dados) | - Delegacia de Crimes Cibernéticos<br>- Telefone: 197 |
| **CERT.br** | Incidentes de segurança de rede | - Email: cert@cert.br<br>- Formulário: www.cert.br |
| **Fornecedores** (Heroku, AWS, Cloudflare) | Vulnerabilidades em infraestrutura | - Suporte técnico de cada fornecedor<br>- Portais de suporte |

---

## 4. Processo de Resposta a Incidentes

### 4.1 Visão Geral do Processo (6 Fases)

```
1. DETECÇÃO → 2. AVALIAÇÃO → 3. CONTENÇÃO → 4. INVESTIGAÇÃO → 5. NOTIFICAÇÃO → 6. RECUPERAÇÃO
     ↓              ↓              ↓               ↓                 ↓                ↓
  0-2 horas     2-6 horas      6-12 horas      12-48 horas       até 72h          1-4 semanas
```

---

### 4.2 FASE 1: Detecção e Identificação (0-2 horas)

**Objetivo:** Identificar e confirmar que um incidente ocorreu.

**Fontes de Detecção:**
- ✅ Alertas de monitoramento de sistema (Heroku, AWS)
- ✅ Relatórios de usuários sobre comportamento anormal
- ✅ Logs de auditoria mostrando atividade suspeita
- ✅ Varreduras de segurança
- ✅ Notificações de fornecedores terceirizados

**Ações Imediatas:**

| # | Ação | Responsável | Prazo |
|---|------|-------------|-------|
| 1 | Documentar data/hora de detecção | Quem detectou | Imediato |
| 2 | Notificar Coordenador de Incidente | Quem detectou | 15 min |
| 3 | Ativar Equipe de Resposta a Incidentes | Coordenador | 30 min |
| 4 | Criar registro de incidente | Coordenador | 1 hora |
| 5 | Fazer avaliação inicial de severidade | Coordenador | 2 horas |

**Template de Registro Inicial:**
```
ID DO INCIDENTE: INC-[AAAA]-[MMM]-[Número]
DATA/HORA DE DETECÇÃO: _______________
DETECTADO POR: _______________
FONTE DE DETECÇÃO: _______________
DESCRIÇÃO INICIAL: _______________
CLASSIFICAÇÃO PRELIMINAR: Nível ___
COORDENADOR DESIGNADO: _______________
```

---

### 4.3 FASE 2: Avaliação e Classificação (2-6 horas)

**Objetivo:** Entender o escopo e impacto do incidente.

**Perguntas Críticas:**

1. **Que dados foram afetados?**
   - Tipo de dados (pessoal, sensível, público)
   - Categorias (usuários, petições, assinaturas)
   - Volume de registros

2. **Quantos titulares foram afetados?**
   - Contagem exata (se possível)
   - Estimativa conservadora
   - Identificação de grupos específicos

3. **Como ocorreu o incidente?**
   - Vetor de ataque
   - Vulnerabilidade explorada
   - Atores envolvidos (se conhecido)

4. **Quando ocorreu?**
   - Data/hora de início
   - Duração da exposição
   - Data/hora de detecção

5. **Qual é o risco para os titulares?**
   - Dano potencial (fraude, constrangimento, etc.)
   - Probabilidade de exploração
   - Medidas de proteção existentes (criptografia, hashing)

**Ações de Avaliação:**

| # | Ação | Responsável | Prazo |
|---|------|-------------|-------|
| 1 | Consultar logs de sistema | Líder Técnico | 2 horas |
| 2 | Identificar dados afetados | Líder Técnico | 3 horas |
| 3 | Estimar número de titulares | Líder Técnico | 4 horas |
| 4 | Avaliar impacto legal | Assessoria Jurídica | 6 horas |
| 5 | Classificar severidade final | Coordenador | 6 horas |
| 6 | Decidir sobre notificações | Coordenador + Jurídico | 6 horas |

---

### 4.4 FASE 3: Contenção (6-12 horas)

**Objetivo:** Parar o incidente e prevenir maior dano.

**Contenção de Curto Prazo (Imediata):**
- 🔴 Isolar sistemas afetados
- 🔴 Bloquear contas comprometidas
- 🔴 Desativar endpoints vulneráveis
- 🔴 Alterar credenciais expostas
- 🔴 Revogar tokens de acesso

**Contenção de Longo Prazo:**
- 🟡 Aplicar patches de segurança
- 🟡 Implementar regras de firewall
- 🟡 Fortalecer controles de acesso
- 🟡 Habilitar logging adicional

**Ações de Contenção:**

| Tipo de Incidente | Ações de Contenção |
|-------------------|--------------------|
| **Acesso Não Autorizado** | - Alterar todas as senhas<br>- Revogar sessões ativas<br>- Bloquear endereços IP maliciosos<br>- Habilitar autenticação de dois fatores |
| **Divulgação de Dados** | - Remover dados expostos (ex: bucket S3 público)<br>- Revogar URLs de compartilhamento<br>- Contactar plataformas de terceiros para remoção |
| **Ransomware/Malware** | - Isolar sistemas infectados da rede<br>- Não pagar resgate<br>- Restaurar de backups limpos |
| **Injeção SQL** | - Desativar endpoint vulnerável<br>- Aplicar parametrização de consultas<br>- Validar todas as entradas |
| **Ataque DDoS** | - Ativar proteção Cloudflare<br>- Ajustar limites de taxa<br>- Bloquear IPs de origem |

**Preservação de Evidências:**
- ✅ Capturar logs antes da rotação
- ✅ Tirar snapshots de banco de dados
- ✅ Documentar estado do sistema
- ✅ Salvar tráfego de in network (se disponível)

---

### 4.5 FASE 4: Investigação e Análise (12-48 horas)

**Objetivo:** Entender completamente a causa raiz e escopo.

**Atividades de Investigação:**

1. **Análise de Logs:**
   - Logs de aplicação Django
   - Logs de acesso de servidor web
   - Logs de banco de dados
   - Logs de auditoria
   - Logs de fornecedores (Heroku, AWS, Cloudflare)

2. **Análise Forense:**
   - Rastrear vetor de ataque
   - Identificar vulnerabilidade explorada
   - Determinar cronograma exato
   - Identificar todos os dados acessados

3. **Análise de Impacto:**
   - Lista completa de titulares afetados
   - Categorias de dados comprometidos
   - Duração da exposição
   - Probabilidade de exploração

**Perguntas a Responder:**
- ❓ Como o atacante obteve acesso inicial?
- ❓ Que privilégios eles obtiveram?
- ❓ Quanto tempo eles tiveram acesso?
- ❓ Que dados eles visualizaram/exfiltraram?
- ❓ Existem backdoors ou persistência?
- ❓ Outros sistemas foram comprometidos?

**Documentação:**
- ✅ Cronograma detalhado de eventos
- ✅ Dados afetados (tabelas, campos, registros)
- ✅ Análise de causa raiz
- ✅ Evidências coletadas
- ✅ Recomendações de remediação

---

### 4.6 FASE 5: Notificação (até 72 horas)

**Objetivo:** Cumprir obrigações legais de notificação.

#### 5.6.1 Notificação à ANPD

**Quando Notificar:**
- ✅ Incidentes de Nível 1 (Crítico) - SEMPRE
- ⚠️ Incidentes de Nível 2 (Alto) - SE risco significativo aos titulares
- ❌ Incidentes de Nível 3-4 - Geralmente não é necessário

**Prazo:** 72 horas da ciência do incidente (LGPD Art. 48)

**Método:** Portal da ANPD (www.gov.br/anpd)

**Conteúdo Obrigatório (LGPD Art. 48, §1º):**

| Requisito | Descrição | Exemplo |
|-----------|-----------|---------|
| **I. Natureza dos Dados** | Tipo de dados pessoais afetados | "CPFs hash (SHA-256), endereços de email, nomes completos" |
| **II. Titulares Envolvidos** | Número e características dos titulares | "Aproximadamente 1.200 signatários de petições ativas" |
| **III. Medidas de Segurança** | Proteções técnicas em vigor | "Dados criptografados em repouso (AES-256), hashing unidirecional de CPFs" |
| **IV. Riscos Relacionados** | Impacto potencial | "Risco baixo de identificação devido ao hashing; risco moderado de spam via email" |
| **V. Motivos de Demora** | Se notificação não foi imediata | "Investigação necessária para determinar escopo exato - 48 horas" |
| **VI. Medidas Corretivas** | Ações tomadas/planejadas | "Credenciais alteradas, endpoint vulnerável corrigido, MFA implementado" |

**Template de Notificação ANPD:** Ver Seção 6.1

#### 5.6.2 Notificação aos Titulares

**Quando Notificar:**
- ✅ Quando há risco significativo aos direitos e liberdades
- ✅ Incidentes de Nível 1 (Crítico)
- ⚠️ Incidentes de Nível 2 (Alto) - avaliação caso a caso

**Prazo:** Razoável, tipicamente dentro de 72 horas

**Método:**
- Email para endereço registrado
- Aviso no site (para grande número de titulares)
- Comunicado de imprensa (se muito grave)

**Conteúdo:**
- Descrição clara e simples do incidente
- Tipos de dados afetados
- Ações tomadas pela Petição Brasil
- Recomendações para os titulares
- Informações de contato para dúvidas
- Pedido de desculpas (se apropriado)

**Template de Notificação a Titulares:** Ver Seção 6.2

#### 5.6.3 Outras Notificações

**Fornecedores/Operadores:**
- Notificar se o incidente originou-se de seus sistemas
- Exigir relatório de incidente e medidas corretivas

**Autoridades Policiais:**
- Notificar se houver suspeita de crime (invasão, fraude)
- Delegacia de Crimes Cibernéticos da Polícia Federal

**Mídia:**
- Considerar comunicado proativo se incidente for grave
- Preparar FAQ para perguntas de imprensa

---

### 4.7 FASE 6: Recuperação e Remediação (1-4 semanas)

**Objetivo:** Restaurar operações normais e prevenir recorrência.

**Atividades de Recuperação:**

| # | Atividade | Responsável | Prazo |
|---|-----------|-------------|-------|
| 1 | Corrigir vulnerabilidade explorada | Líder Técnico | 1 semana |
| 2 | Aplicar patches e atualizações | Líder Técnico | 1 semana |
| 3 | Fortalecer controles de segurança | Líder Técnico | 2 semanas |
| 4 | Implementar monitoramento adicional | Líder Técnico | 2 semanas |
| 5 | Revisar e atualizar políticas | Coordenador | 3 semanas |
| 6 | Conduzir treinamento de equipe | Coordenador | 4 semanas |
| 7 | Testar medidas de remediação | Líder Técnico | 4 semanas |

**Medidas de Prevenção:**

| Tipo de Incidente | Medidas de Prevenção |
|-------------------|----------------------|
| **Acesso Não Autorizado** | - Implementar MFA<br>- Fortalecer política de senhas<br>- Revisão regular de permissões |
| **Divulgação de Dados** | - Configuração de segurança padrão em S3<br>- Revisão de compartilhamentos públicos<br>- Política de classificação de dados |
| **Injeção SQL** | - Usar sempre ORM Django<br>- Validação rigorosa de entrada<br>- Revisão de código |
| **Ransomware** | - Backups offline regulares<br>- Filtros de email<br>- Atualizações de segurança |

**Lições Aprendidas:**
- Reunião pós-incidente com equipe de resposta
- Documentar o que funcionou e o que não funcionou
- Atualizar este plano com melhorias
- Compartilhar conhecimento com equipe mais ampla

---

## 5. Monitoramento e Detecção Proativa

### 5.1 Fontes de Monitoramento

| Fonte | Frequência de Verificação | Responsável | Alertas Automáticos? |
|-------|---------------------------|-------------|----------------------|
| **Logs de Aplicação Django** | Diário | Líder Técnico | Sim (erros 500) |
| **Logs de Acesso** | Semanal | Líder Técnico | Não |
| **Logs de Auditoria** | Semanal | Encarregado | Não |
| **Heroku Metrics** | Diário | Líder Técnico | Sim (downtime) |
| **AWS CloudWatch** | Diário | Líder Técnico | Sim (anomalias) |
| **Cloudflare Analytics** | Semanal | Líder Técnico | Sim (ataques DDoS) |
| **Relatórios de Usuários** | Contínuo | Todos | N/A |

### 5.2 Indicadores de Comprometimento (IoC)

**Sinais de Alerta:**
- 🚨 Múltiplas tentativas de login falhadas
- 🚨 Acessos de localizações geográficas incomuns
- 🚨 Acessos fora do horário comercial
- 🚨 Grandes volumes de download de dados
- 🚨 Modificações inesperadas de registros
- 🚨 Novos usuários administrativos criados
- 🚨 Tráfego anormal de rede
- 🚨 Processos desconhecidos em execução
- 🚨 Alterações não autorizadas de configuração

**Ações Automáticas:**
- Bloqueio temporário de conta após 5 tentativas de login falhadas
- Alerta de email para admin em erros 500
- Limitação de taxa em endpoints de API

---

## 6. Templates de Comunicação

### 6.1 Template de Notificação à ANPD

```
ASSUNTO: Notificação de Incidente de Segurança de Dados - [ID do Incidente]

À Autoridade Nacional de Proteção de Dados (ANPD),

A Petição Brasil, atuando como controladora de dados, comunica formalmente a ocorrência de um incidente de segurança de dados pessoais, conforme exigido pelo Art. 48 da Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018).

**1. IDENTIFICAÇÃO DO CONTROLADOR**
Nome: Petição Brasil
Encarregado: [Nome]
Email: contato@peticaobrasil.com.br
CNPJ: [Número]

**2. IDENTIFICAÇÃO DO INCIDENTE**
ID do Incidente: [INC-AAAA-MMM-Número]
Data de Ocorrência: [Data e hora]
Data de Detecção: [Data e hora]
Data desta Notificação: [Data]

**3. NATUREZA DOS DADOS PESSOAIS AFETADOS (Art. 48, §1º, I)**
Categorias de Dados:
- [Ex: Nomes completos]
- [Ex: Endereços de email]
- [Ex: Hashes de CPF (SHA-256)]
- [Ex: Cidades/estados de residência]

Dados Sensíveis Afetados: [Sim/Não]
Se sim, especificar: [Descrição]

**4. TITULARES ENVOLVIDOS (Art. 48, §1º, II)**
Número Estimado de Titulares Afetados: [Número ou faixa]
Características dos Titulares: [Ex: Signatários de petições públicas]
Possibilidade de Identificação: [Alta/Média/Baixa]

**5. MEDIDAS TÉCNICAS DE SEGURANÇA (Art. 48, §1º, III)**
Proteções Implementadas Antes do Incidente:
- [Ex: Criptografia em repouso (AES-256)]
- [Ex: Hashing unidirecional de CPFs (SHA-256)]
- [Ex: Conexões HTTPS (TLS 1.2+)]
- [Ex: Controle de acesso baseado em função]

**6. RISCOS RELACIONADOS AO INCIDENTE (Art. 48, §1º, IV)**
Probabilidade de Dano aos Titulares: [Alta/Média/Baixa]
Tipos de Dano Potencial:
- [Ex: Spam por email]
- [Ex: Risco mínimo de identificação devido ao hashing]
- [Ex: Sem risco financeiro direto]

Avaliação Geral de Risco: [Crítico/Alto/Médio/Baixo]

**7. MOTIVOS DE DEMORA (Art. 48, §1º, V)**
[Se notificação não for imediata, explicar:]
[Ex: "Investigação técnica necessária para determinar escopo exato de dados afetados - 36 horas"]
[Ou: "N/A - Notificação dentro do prazo de 72 horas"]

**8. MEDIDAS ADOTADAS (Art. 48, §1º, VI)**

Contenção (já implementada):
- [Ex: Credenciais de admin alteradas imediatamente]
- [Ex: Endpoint vulnerável desativado]
- [Ex: IPs maliciosos bloqueados]

Remediação (em andamento):
- [Ex: Patch de segurança aplicado]
- [Ex: Autenticação de dois fatores implementada]
- [Ex: Auditoria de segurança completa agendada]

Prevenção (planejada):
- [Ex: Revisão mensal de configurações de segurança]
- [Ex: Treinamento de equipe em segurança cibernética]
- [Ex: Implementação de monitoramento 24/7]

**9. CRONOGRAMA DE EVENTOS**
[Data/Hora] - Incidente ocorreu
[Data/Hora] - Incidente detectado
[Data/Hora] - Equipe de resposta ativada
[Data/Hora] - Contenção concluída
[Data/Hora] - Notificação aos titulares (se aplicável)
[Data/Hora] - Esta notificação à ANPD

**10. NOTIFICAÇÃO AOS TITULARES**
Titulares foram notificados? [Sim/Não]
Se sim, data e método: [Descrição]
Se não, justificativa: [Explicação]

**11. INFORMAÇÕES ADICIONAIS**
[Qualquer informação relevante adicional]

**12. CONTATO PARA ESCLARECIMENTOS**
Encarregado: [Nome completo]
Email: contato@peticaobrasil.com.br
Telefone: [Número, se disponível]

Atenciosamente,
[Nome do Encarregado]
Encarregado de Proteção de Dados
Petição Brasil

Data: [Data]
```

---

### 6.2 Template de Notificação aos Titulares

**VERSÃO 1: Email Individual (para pequeno número de titulares)**

```
ASSUNTO: Importante: Incidente de Segurança de Dados - Petição Brasil

Prezado(a) [Nome],

Escrevemos para informá-lo(a) sobre um incidente de segurança que pode ter afetado seus dados pessoais na plataforma Petição Brasil.

**O QUE ACONTECEU?**
[Descrição clara e simples do incidente, sem jargão técnico]
[Ex: "Em [data], detectamos acesso não autorizado a nosso sistema que resultou na exposição de dados de assinantes de petições."]

**QUE DADOS FORAM AFETADOS?**
Seus dados que podem ter sido afetados incluem:
- [Ex: Seu nome completo]
- [Ex: Seu endereço de email]
- [Ex: Sua cidade e estado]
- [Ex: Data em que você assinou petições]

IMPORTANTE: [Esclarecer dados que NÃO foram afetados]
[Ex: "Seus CPFs são armazenados apenas em formato hash (criptografado irreversível) e não podem ser convertidos de volta para o número original."]

**O QUE ESTAMOS FAZENDO?**
- [Ex: Fechamos imediatamente a vulnerabilidade que permitiu o acesso]
- [Ex: Alteramos todas as credenciais de administrador]
- [Ex: Implementamos autenticação de dois fatores]
- [Ex: Estamos conduzindo uma auditoria completa de segurança]
- [Ex: Notificamos a Autoridade Nacional de Proteção de Dados (ANPD)]

**O QUE VOCÊ DEVE FAZER?**
- [Recomendações específicas, se houver]
- [Ex: "Fique atento a emails de phishing que possam usar seu nome"]
- [Ex: "Não compartilhe senhas ou dados pessoais por email"]
- [Ex: "Monitore sua caixa de entrada de spam"]

[Se houver risco baixo:]
"Com base em nossa análise, acreditamos que o risco aos seus dados é baixo devido às medidas de segurança que tínhamos em vigor (criptografia, hashing). No entanto, queríamos informá-lo(a) por transparência."

**PERGUNTAS?**
Se você tiver dúvidas ou preocupações, entre em contato conosco:
Email: contato@peticaobrasil.com.br
Responderemos dentro de 48 horas.

**NOSSO COMPROMISSO**
Levamos a segurança de seus dados muito a sério. Este incidente nos ensinou lições valiosas e estamos implementando medidas adicionais para garantir que não aconteça novamente.

Pedimos sinceras desculpas pelo incômodo e preocupação que isso possa ter causado.

Atenciosamente,
Equipe Petição Brasil

---
Encarregado de Dados: contato@peticaobrasil.com.br
Data: [Data]
```

**VERSÃO 2: Aviso no Site (para grande número de titulares)**

```
[Banner destacado no topo do site]

⚠️ AVISO IMPORTANTE DE SEGURANÇA

Em [data], detectamos um incidente de segurança que afetou dados de aproximadamente [número] usuários. 
Dados afetados: [lista resumida]. 
Ação imediata tomada: [resumo].
Leia mais » [link para página detalhada]

[Página detalhada - /security-incident]

# Notificação de Incidente de Segurança

**Atualizado em:** [Data e hora]

## Resumo
Em [data], a Petição Brasil detectou [descrição breve do incidente]. Tomamos ação imediata para conter o incidente e proteger seus dados.

## Cronograma
- **[Data/hora]:** Incidente detectado
- **[Data/hora]:** Contenção implementada
- **[Data/hora]:** Vulnerabilidade corrigida
- **[Data/hora]:** Notificação aos afetados iniciada

## Dados Afetados
[Lista detalhada dos tipos de dados]

## Dados NÃO Afetados
[Lista de dados que permanecem seguros]

## Ações Tomadas
[Lista detalhada de medidas de contenção, remediação e prevenção]

## Você Foi Afetado?
[Se possível, oferecer ferramenta de verificação ou instruções]

## Próximos Passos
[O que a Petição Brasil fará]
[O que os usuários devem fazer]

## Perguntas Frequentes

**P: Meu CPF foi exposto?**
R: Não. CPFs são armazenados apenas em formato hash irreversível.

**P: Devo alterar minha senha?**
R: [Sim/Não e por quê]

**P: Posso continuar usando a plataforma?**
R: Sim. O incidente foi contido e a plataforma está segura.

**P: Vocês vão me compensar?**
R: [Política de compensação, se aplicável]

## Contato
Email: contato@peticaobrasil.com.br
Resposta em: 48 horas

Pedimos desculpas pelo ocorrido e agradecemos sua compreensão.

Equipe Petição Brasil
```

---

### 6.3 Template de Relatório Pós-Incidente

```
# RELATÓRIO PÓS-INCIDENTE DE SEGURANÇA DE DADOS

**ID do Incidente:** [INC-AAAA-MMM-Número]  
**Data do Incidente:** [Data]  
**Data deste Relatório:** [Data]  
**Preparado por:** [Nome do Coordenador]  
**Classificação:** Interno - Confidencial

---

## 1. RESUMO EXECUTIVO
[Descrição de 2-3 parágrafos do incidente, impacto e resolução]

**Severidade:** [Nível 1-4]  
**Titulares Afetados:** [Número]  
**Custo Total:** R$ [Valor] (estimado)  
**Status:** [Resolvido/Em andamento]

---

## 2. DETALHES DO INCIDENTE

### 2.1 Descoberta
**Data/Hora de Ocorrência:** [Quando realmente aconteceu]  
**Data/Hora de Detecção:** [Quando descobrimos]  
**Tempo para Detecção:** [Diferença]  
**Detectado por:** [Pessoa/sistema]  
**Método de Detecção:** [Como foi descoberto]

### 2.2 Natureza do Incidente
**Tipo:** [Ex: Acesso não autorizado, divulgação de dados, etc.]  
**Vetor de Ataque:** [Como o incidente ocorreu]  
**Vulnerabilidade Explorada:** [Falha de segurança específica]  
**Atores:** [Internos/externos, intencionais/acidentais]

### 2.3 Dados Afetados
**Categorias:** [Usuários, petições, assinaturas, etc.]  
**Campos Específicos:** [Tabela de dados comprometidos]  
**Volume:** [Número de registros]  
**Sensibilidade:** [Pessoal/sensível]

---

## 3. CRONOGRAMA DETALHADO

| Data/Hora | Evento | Responsável |
|-----------|--------|-------------|
| [DH] | Incidente ocorreu | - |
| [DH] | Incidente detectado | [Nome] |
| [DH] | Equipe ativada | [Nome] |
| [DH] | Contenção iniciada | [Nome] |
| [DH] | Contenção concluída | [Nome] |
| [DH] | Investigação concluída | [Nome] |
| [DH] | ANPD notificada | [Nome] |
| [DH] | Titulares notificados | [Nome] |
| [DH] | Remediação concluída | [Nome] |

**Tempo Total de Resposta:** [Detecção até resolução]

---

## 4. ANÁLISE DE CAUSA RAIZ

### 4.1 Causa Imediata
[O que diretamente causou o incidente]

### 4.2 Causas Contribuintes
- [Fator 1]
- [Fator 2]
- [Fator 3]

### 4.3 Causa Raiz
[A razão fundamental pela qual o incidente foi possível]

### 4.4 Diagrama de Análise (5 Porquês)
1. **Por que [incidente] aconteceu?** → [Resposta]
2. **Por que [resposta 1]?** → [Resposta]
3. **Por que [resposta 2]?** → [Resposta]
4. **Por que [resposta 3]?** → [Resposta]
5. **Por que [resposta 4]?** → [CAUSA RAIZ]

---

## 5. RESPOSTA E CONTENÇÃO

### 5.1 Ações de Contenção
[Lista de medidas tomadas para parar o incidente]

### 5.2 Eficácia
[O que funcionou bem / o que não funcionou]

### 5.3 Tempo de Contenção
**Planejado:** [Expectativa]  
**Real:** [Tempo efetivo]  
**Variação:** [Diferença e motivo]

---

## 6. IMPACTO

### 6.1 Impacto nos Titulares
**Titulares Afetados:** [Número exato]  
**Risco de Dano:** [Alto/Médio/Baixo]  
**Danos Reais Relatados:** [Se houver]

### 6.2 Impacto Operacional
**Downtime:** [Duração]  
**Funcionalidades Afetadas:** [Lista]  
**Usuários Impactados:** [Número]

### 6.3 Impacto Financeiro
| Item | Custo |
|------|-------|
| Tempo de equipe | R$ [Valor] |
| Consultoria externa | R$ [Valor] |
| Medidas de remediação | R$ [Valor] |
| Perda de receita | R$ [Valor] |
| **Total Estimado** | **R$ [Valor]** |

### 6.4 Impacto Reputacional
[Avaliação de dano à marca e confiança do usuário]

---

## 7. LIÇÕES APRENDIDAS

### 7.1 O Que Funcionou Bem
- [Aspecto positivo 1]
- [Aspecto positivo 2]
- [Aspecto positivo 3]

### 7.2 O Que Pode Melhorar
- [Área de melhoria 1]
- [Área de melhoria 2]
- [Área de melhoria 3]

### 7.3 Surpresas
[Aspectos inesperados do incidente ou resposta]

---

## 8. ITENS DE AÇÃO

| # | Ação | Responsável | Prazo | Status |
|---|------|-------------|-------|--------|
| 1 | [Ação corretiva específica] | [Nome] | [Data] | [Status] |
| 2 | [Melhoria de processo] | [Nome] | [Data] | [Status] |
| 3 | [Atualização de documentação] | [Nome] | [Data] | [Status] |

---

## 9. RECOMENDAÇÕES

### 9.1 Técnicas
- [Recomendação técnica 1]
- [Recomendação técnica 2]

### 9.2 Processuais
- [Recomendação de processo 1]
- [Recomendação de processo 2]

### 9.3 Treinamento
- [Necessidade de treinamento 1]
- [Necessidade de treinamento 2]

---

## 10. ANEXOS
- Anexo A: Logs de sistema relevantes
- Anexo B: Comunicação com ANPD
- Anexo C: Notificações aos titulares
- Anexo D: Análise forense detalhada

---

**Aprovado por:** [Nome do Encarregado]  
**Data:** [Data]
```

---

## 7. Treinamento e Conscientização

### 7.1 Treinamento da Equipe

**Frequência:** Anual (mínimo) + quando houver incidente significativo

**Conteúdo do Treinamento:**
- Visão geral da LGPD e obrigações
- Identificação de incidentes de segurança
- Procedimentos de notificação
- Papéis e responsabilidades
- Simulações de incidente (tabletop exercises)
- Lições aprendidas de incidentes passados

**Público:**
- Todos os administradores
- Equipe técnica
- Moderadores
- Encarregado

### 7.2 Exercícios de Simulação

**Frequência:** Anual

**Cenários de Prática:**
1. **Cenário 1:** Bucket S3 configurado como público acidentalmente
2. **Cenário 2:** Credenciais de admin comprometidas por phishing
3. **Cenário 3:** Injeção SQL em formulário de busca
4. **Cenário 4:** Ransomware em servidor de aplicação

**Avaliação:**
- Tempo de detecção
- Eficácia de contenção
- Qualidade de comunicação
- Conformidade com procedimentos

---

## 8. Manutenção deste Plano

### 8.1 Revisão e Atualização

**Frequência de Revisão:** Semestral (a cada 6 meses)

**Gatilhos para Revisão Imediata:**
- Após qualquer incidente real
- Mudanças na legislação (LGPD, regulamentações da ANPD)
- Mudanças significativas na arquitetura de sistema
- Novos operadores de dados
- Lições aprendidas de incidentes no setor

**Responsável pela Atualização:** Encarregado de Dados

### 8.2 Distribuição

**Quem Deve Ter Cópia:**
- Encarregado de Dados
- Administradores de sistema
- Assessoria jurídica
- Administração superior

**Local de Armazenamento:**
- Versão digital: `/DOCS/legal_docs/incident-response-plan.md`
- Versão impressa: [Local seguro e acessível]

### 8.3 Controle de Versão

| Versão | Data | Alterações | Atualizado por |
|--------|------|------------|----------------|
| 1.0 | 25/01/2026 | Criação inicial | Encarregado |

---

## 9. Referências

### 9.1 Legislação

- **LGPD:** Lei 13.709/2018 (especialmente Art. 48)
- **Marco Civil da Internet:** Lei 12.965/2014 (Art. 15 - retenção de logs)
- **Decreto 10.543/2020:** Regulamentação do Gov.br e assinaturas digitais

### 9.2 Orientações da ANPD

- Guia Orientativo para Definições dos Agentes de Tratamento de Dados Pessoais e do Encarregado
- Guia Orientativo de Segurança da Informação

### 9.3 Padrões de Mercado

- ISO/IEC 27035: Gestão de Incidentes de Segurança da Informação
- NIST Cybersecurity Framework: Incident Response
- SANS Incident Handler's Handbook

---

## 10. Aprovação

**Este Plano de Resposta a Incidentes foi revisado e aprovado em 25 de janeiro de 2026.**

**Aprovado por:** Encarregado de Dados - Petição Brasil  
**Data:** 25 de janeiro de 2026  
**Próxima Revisão:** Julho de 2026

---

**Status do Documento:** Ativo  
**Classificação:** Interno - Confidencial  
**Versão:** 1.0
