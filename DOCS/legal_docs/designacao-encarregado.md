# Designação Formal do Encarregado de Dados (DPO)
**Petição Brasil - Lei Geral de Proteção de Dados**

**Tipo de Documento:** Conformidade Legal (LGPD Art. 41)  
**Data de Designação:** 25 de janeiro de 2026  
**Validade:** Indeterminada (até nova designação)  
**Classificação:** Interno - Conformidade Legal

---

## 1. Base Legal

A Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018), em seu Artigo 41, estabelece:

> **Art. 41.** O controlador deverá indicar encarregado pelo tratamento de dados pessoais.
> 
> **§ 1º** A identidade e as informações de contato do encarregado deverão ser divulgadas publicamente, de forma clara e objetiva, preferencialmente no sítio eletrônico do controlador.
> 
> **§ 2º** As atividades do encarregado consistem em:
> 
> I - aceitar reclamações e comunicações dos titulares, prestar esclarecimentos e adotar providências;
> 
> II - receber comunicações da autoridade nacional e adotar providências;
> 
> III - orientar os funcionários e os contratados da entidade a respeito das práticas a serem tomadas em relação à proteção de dados pessoais; e
> 
> IV - executar as demais atribuições determinadas pelo controlador ou estabelecidas em normas complementares.

---

## 2. Designação Oficial

### 2.1 Identificação do Controlador

**Nome da Organização:** Petição Brasil  
**Natureza Jurídica:** Plataforma Digital para Participação Democrática  
**Atividade Principal:** Gestão de petições online com assinaturas digitais  
**CNPJ:** [A preencher quando disponível]  
**Endereço:** [A preencher quando disponível]

### 2.2 Encarregado Designado

**Nome/Designação:** Administrador da Plataforma Petição Brasil  
**Cargo:** Encarregado de Proteção de Dados (Data Protection Officer - DPO)  
**Email Oficial:** contato@peticaobrasil.com.br  
**Telefone:** [Opcional - pode ser omitido para organizações pequenas]  
**Data de Designação:** 25 de janeiro de 2026  
**Status:** Designação interna (permitido para organizações de pequeno porte)

### 2.3 Justificativa para Designação Interna

De acordo com a interpretação regulatória da ANPD (Autoridade Nacional de Proteção de Dados), organizações de pequeno e médio porte podem designar um membro existente da equipe como Encarregado, desde que:

1. ✅ A pessoa possua conhecimento adequado sobre LGPD e proteção de dados
2. ✅ Não haja conflito de interesses (o Encarregado pode acumular funções desde que possa atuar de forma independente em questões de privacidade)
3. ✅ As informações de contato sejam publicamente divulgadas
4. ✅ O Encarregado tenha recursos adequados para desempenhar suas funções

**Status da Petição Brasil:** Plataforma de pequeno porte com equipe administrativa limitada, justificando a designação interna ao invés de contratação de DPO dedicado.

---

## 3. Responsabilidades do Encarregado

### 3.1 Responsabilidades Primárias (LGPD Art. 41, §2º)

#### I. Comunicação com Titulares de Dados
- ✅ Receber e processar solicitações de direitos dos titulares (acesso, correção, exclusão, portabilidade, etc.)
- ✅ Fornecer respostas claras e completas dentro do prazo de 15 dias
- ✅ Documentar todas as solicitações e respostas
- ✅ Implementar decisões sobre exercício de direitos

**Canal de Comunicação:** contato@peticaobrasil.com.br  
**SLA de Resposta:** 15 dias corridos (primeira resposta)

#### II. Ligação com a ANPD
- ✅ Servir como ponto de contato oficial com a Autoridade Nacional de Proteção de Dados
- ✅ Responder a consultas e solicitações da ANPD
- ✅ Notificar a ANPD sobre violações de dados dentro de 72 horas (quando aplicável)
- ✅ Submeter documentação de conformidade quando solicitado

**Contato ANPD:** Através do portal oficial (www.gov.br/anpd)

#### III. Orientação e Treinamento Interno
- ✅ Orientar equipe administrativa sobre práticas de proteção de dados
- ✅ Revisar e atualizar políticas de privacidade
- ✅ Conduzir verificações internas de conformidade
- ✅ Fornecer orientação sobre novas atividades de tratamento de dados

**Frequência de Treinamento:** Anual (mínimo) ou quando houver mudanças significativas

#### IV. Outras Atribuições
- ✅ Manter o Registro de Atividades de Tratamento (ROPA)
- ✅ Gerenciar relações com operadores de dados (fornecedores)
- ✅ Supervisionar resposta a incidentes de segurança
- ✅ Recomendar medidas de conformidade à administração

### 3.2 Responsabilidades Operacionais Detalhadas

#### Gestão de Solicitações de Titulares

| Tipo de Solicitação | Procedimento | Prazo | Responsável |
|---------------------|--------------|-------|-------------|
| **Confirmação de Tratamento** | Verificar ROPA, responder por email | 15 dias | Encarregado |
| **Acesso aos Dados** | Exportar dados do BD, enviar JSON/PDF | 15 dias | Encarregado + Técnico |
| **Correção de Dados** | Atualizar registros, confirmar por email | 10 dias | Encarregado + Técnico |
| **Exclusão/Anonimização** | Processar conforme política de retenção | 15 dias | Encarregado + Técnico |
| **Portabilidade** | Exportar dados estruturados (JSON) | 15 dias | Encarregado + Técnico |
| **Revogação de Consentimento** | Interromper tratamento, confirmar | 5 dias | Encarregado |
| **Oposição ao Tratamento** | Avaliar base legal, responder | 15 dias | Encarregado + Jurídico |
| **Revisão de Decisão Automatizada** | N/A (sem decisões automatizadas) | - | - |

#### Gestão de Incidentes de Dados

**Gatilhos de Notificação:**
- Acesso não autorizado a dados pessoais
- Vazamento ou exposição de dados
- Perda de dados
- Modificação não autorizada de dados
- Disponibilidade comprometida de dados críticos

**Processo de Resposta:**
1. **Detecção** (0-2 horas): Identificar e classificar incidente
2. **Contenção** (2-6 horas): Interromper violação, proteger dados restantes
3. **Avaliação** (6-24 horas): Determinar impacto, risco aos titulares
4. **Notificação** (até 72 horas): Notificar ANPD se alto risco
5. **Comunicação** (até 72 horas): Notificar titulares afetados se risco significativo
6. **Remediação** (1-2 semanas): Corrigir vulnerabilidades
7. **Documentação** (2 semanas): Registrar incidente, lições aprendidas

**Critérios para Notificação da ANPD:**
- Risco significativo aos direitos e liberdades dos titulares
- Possível dano material ou moral
- Violação envolvendo dados sensíveis
- Grande número de titulares afetados

#### Manutenção de Conformidade

**Tarefas Trimestrais:**
- ✅ Revisar e atualizar ROPA (Registro de Atividades de Tratamento)
- ✅ Verificar status de DPAs com operadores terceirizados
- ✅ Revisar logs de acesso e auditoria
- ✅ Verificar conformidade de retenção de dados

**Tarefas Anuais:**
- ✅ Revisar e atualizar Política de Privacidade
- ✅ Revisar e atualizar Termos de Uso
- ✅ Conduzir treinamento de equipe
- ✅ Auditar medidas de segurança técnica
- ✅ Avaliar necessidade de DPIA (Avaliação de Impacto)
- ✅ Renovar/revisar DPAs com fornecedores

**Tarefas Ad Hoc:**
- ✅ Avaliar novas atividades de tratamento de dados
- ✅ Revisar integrações com novos fornecedores
- ✅ Responder a auditorias ou inspeções da ANPD
- ✅ Implementar mudanças em regulamentações

---

## 4. Divulgação Pública

### 4.1 Conformidade com LGPD Art. 41, §1º

As informações de contato do Encarregado foram divulgadas publicamente nos seguintes locais:

✅ **Política de Privacidade** (https://peticaobrasil.com.br/privacy/)  
   - Seção 14: "Encarregado de Dados (LGPD)"
   - Informações completas de contato
   - Descrição das responsabilidades

✅ **Termos de Uso** (https://peticaobrasil.com.br/terms/)  
   - Seção 7: Referência aos direitos LGPD
   - Instruções para contato com Encarregado

✅ **Rodapé do Site**  
   - [A implementar]: Link direto para contato do Encarregado

### 4.2 Formato de Divulgação

```
Encarregado de Dados (DPO)
Email: contato@peticaobrasil.com.br

Para exercer seus direitos sob a LGPD (acesso, correção, exclusão, 
portabilidade, etc.), envie um email para o endereço acima.

Prazo de resposta: 15 dias corridos
```

---

## 5. Recursos e Suporte

### 5.1 Recursos Disponíveis

**Documentação:**
- ✅ ROPA (Registro de Atividades de Tratamento)
- ✅ Política de Privacidade
- ✅ Plano de Resposta a Incidentes
- ✅ Acordos de Processamento de Dados (DPAs)

**Ferramentas:**
- ✅ Acesso administrativo ao Django Admin
- ✅ Acesso ao banco de dados (somente leitura para verificações)
- ✅ Logs de auditoria e segurança
- ✅ Email corporativo (contato@peticaobrasil.com.br)

**Suporte Externo:**
- ⚠️ Assessoria jurídica (consultor externo, quando necessário)
- ⚠️ Suporte técnico de fornecedores (Heroku, AWS, Cloudflare)
- ⚠️ Recursos online da ANPD

### 5.2 Orçamento e Tempo

**Tempo Estimado de Dedicação:**
- Rotina: 2-4 horas/semana
- Solicitações de titulares: 1-3 horas por solicitação
- Incidentes: Variável (pode exigir dedicação integral)
- Projetos de conformidade: Conforme necessário

**Orçamento para Conformidade:**
- Treinamento: R$ 500-1.000/ano
- Assessoria jurídica: R$ 2.000-5.000/ano (conforme necessário)
- Ferramentas/software: Incluído na infraestrutura existente

---

## 6. Independência e Autonomia

### 6.1 Salvaguardas de Independência

Embora o Encarregado seja designado internamente, as seguintes salvaguardas garantem independência operacional:

1. ✅ **Comunicação Direta com ANPD:** O Encarregado pode comunicar-se diretamente com a ANPD sem aprovação prévia
2. ✅ **Decisões de Conformidade:** O Encarregado tem autoridade final sobre questões de privacidade e proteção de dados
3. ✅ **Sem Retaliação:** O Encarregado não pode ser penalizado por decisões de conformidade de boa-fé
4. ✅ **Acesso a Recursos:** O Encarregado tem acesso a todos os sistemas e documentação necessários

### 6.2 Gerenciamento de Conflitos de Interesse

**Situações de Potencial Conflito:**
- Decisões que afetam operações da plataforma vs. direitos de privacidade
- Solicitações de exclusão que afetam petições ativas
- Custos de conformidade vs. restrições orçamentárias

**Protocolo de Resolução:**
1. Documentar o conflito
2. Consultar assessoria jurídica quando necessário
3. Priorizar conformidade legal sobre conveniência operacional
4. Escalar para administração superior se não resolvido
5. Documentar decisão e justificativa

---

## 7. Qualificações e Treinamento

### 7.1 Conhecimento Atual

**Familiaridade Legal:**
- ✅ LGPD (Lei 13.709/2018) - texto completo
- ✅ Marco Civil da Internet (Lei 12.965/2014)
- ✅ Regulamentações da ANPD
- ✅ Melhores práticas internacionais (GDPR como referência)

**Conhecimento Técnico:**
- ✅ Arquitetura da plataforma Django
- ✅ Estrutura de banco de dados PostgreSQL
- ✅ Medidas de segurança implementadas
- ✅ Fluxos de tratamento de dados

### 7.2 Treinamento Planejado

**Curto Prazo (2026):**
- [ ] Curso online LGPD certificado (20-40 horas)
- [ ] Webinars da ANPD sobre conformidade
- [ ] Revisão de casos práticos de DPOs

**Médio Prazo (2027):**
- [ ] Certificação profissional em Proteção de Dados (EXIN, IAPP, etc.)
- [ ] Participação em conferências de privacidade
- [ ] Networking com outros DPOs brasileiros

---

## 8. Sucessão e Continuidade

### 8.1 Plano de Sucessão

**Gatilhos para Nova Designação:**
- Renúncia do Encarregado atual
- Reestruturação organizacional
- Conflito de interesses insuperável
- Crescimento que justifique DPO dedicado

**Processo de Transição:**
1. Designação de novo Encarregado
2. Transferência de documentação
3. Atualização de informações de contato públicas
4. Notificação à ANPD (se aplicável)
5. Comunicação aos titulares (via site)

### 8.2 Backup e Contingência

**Responsável Secundário:** [A designar quando equipe crescer]  
**Durante Ausência Temporária:** Email monitorado por administrador da plataforma  
**Acesso de Emergência:** Credenciais de admin compartilhadas em cofre seguro

---

## 9. Registro de Atividades do Encarregado

### 9.1 Solicitações de Titulares (2026)

| Data | ID Solicitação | Tipo | Status | Prazo | Notas |
|------|----------------|------|--------|-------|-------|
| - | - | - | - | - | Nenhuma solicitação recebida ainda |

### 9.2 Comunicações com ANPD

| Data | Tipo | Assunto | Resultado | Notas |
|------|------|---------|-----------|-------|
| - | - | - | - | Nenhuma comunicação ainda |

### 9.3 Incidentes de Dados

| Data | Tipo | Severidade | Notificação ANPD? | Resolução | Notas |
|------|------|------------|-------------------|-----------|-------|
| - | - | - | - | - | Nenhum incidente registrado |

### 9.4 Revisões de Conformidade

| Data | Tipo de Revisão | Resultados | Ações Necessárias |
|------|-----------------|------------|-------------------|
| 25/01/2026 | ROPA Inicial | Concluído | Nenhuma |
| 25/01/2026 | Designação DPO | Concluído | Publicar no site |

---

## 10. Declaração de Aceitação

**Eu, administrador da Petição Brasil, aceito formalmente a designação como Encarregado de Proteção de Dados (DPO) e comprometo-me a:**

1. ✅ Desempenhar todas as responsabilidades listadas neste documento
2. ✅ Agir com independência e priorizar conformidade legal
3. ✅ Manter conhecimento atualizado sobre LGPD e proteção de dados
4. ✅ Servir como ponto de contato para titulares e ANPD
5. ✅ Documentar todas as atividades de conformidade
6. ✅ Notificar violações de dados conforme exigido por lei
7. ✅ Revisar e atualizar políticas de privacidade regularmente

**Data de Aceitação:** 25 de janeiro de 2026  
**Assinatura:** [Digital ou manuscrita quando formalizado]  
**Nome Completo:** [A preencher]  
**CPF:** [A preencher]

---

## 11. Aprovação Organizacional

**Esta designação foi aprovada pela administração da Petição Brasil em 25 de janeiro de 2026.**

**Aprovado por:** [Administração]  
**Data:** 25 de janeiro de 2026  
**Vigência:** Indeterminada até nova designação

---

## 12. Anexos

- **Anexo A:** ROPA (Registro de Atividades de Tratamento) - `/DOCS/legal_docs/data-mapping-ropa.md`
- **Anexo B:** Plano de Resposta a Incidentes - `/DOCS/legal_docs/incident-response-plan.md` [A criar]
- **Anexo C:** Política de Privacidade - `/templates/static_pages/privacy.html`
- **Anexo D:** DPAs com Operadores - `/DOCS/legal_docs/processor-agreements/` [A preencher]

---

**Status do Documento:** Ativo  
**Classificação:** Interno - Conformidade Legal  
**Próxima Revisão:** Janeiro de 2027 (anual)  
**Local de Armazenamento:** `/DOCS/legal_docs/designacao-encarregado.md`
