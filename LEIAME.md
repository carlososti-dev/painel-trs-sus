# App "Diálise no SUS" — painel + chat

Site com duas páginas:

- `index.html` — o painel (Brasil e por estado), igual ao publicado no Claude.
- `chat.html` — "Pergunte aos dados": perguntas em linguagem natural respondidas pelo Claude
  a partir destes mesmos dados, com as consultas usadas visíveis.

Os dados ficam em `dados/` (tabelas agregadas, sem informação individual de pacientes).
O painel funciona como site estático. O chat precisa de um pequeno servidor que guarda a chave
da API da Anthropic (`api/claude.js` na Vercel, ou `servidor_local.py` no seu computador).

## 1. Testar no seu Mac

```
cd ~/Dev/sus/webapp
export ANTHROPIC_API_KEY="sua-chave-da-api"     # obtenha em console.anthropic.com
export CODIGO_ACESSO="demo2026"                 # opcional: senha para usar o chat
./executar_webapp.sh
```

Abre em http://localhost:8000. Sem a chave, o painel funciona e o chat avisa que não está configurado.

## 2. Publicar para o cliente (Vercel, gratuito)

Precisa de Node.js instalado (https://nodejs.org) e de uma conta na Vercel.

```
cd ~/Dev/sus/webapp
npx vercel            # primeira vez: faz login e cria o projeto (aceite as opções padrão)
npx vercel env add ANTHROPIC_API_KEY     # cole a chave quando pedir (Production)
npx vercel env add CODIGO_ACESSO         # recomendado: senha que você passa ao cliente
npx vercel --prod     # publica e mostra o link final
```

Alternativa sem linha de comando: suba esta pasta para um repositório no GitHub e importe
em vercel.com/new; depois configure as duas variáveis em Settings › Environment Variables.

## Custos e segurança

- Cada pergunta no chat chama a API da Anthropic na **sua** conta (algumas chamadas por pergunta).
  Defina um limite de gasto no console da Anthropic.
- A chave fica só no servidor (variável de ambiente); nunca vai para o navegador.
- Com `CODIGO_ACESSO` definido, só quem tem o código usa o chat. O painel continua aberto a
  quem tiver o link — os dados são públicos e agregados.
- Modelo usado: `claude-sonnet-5-5` (mude com a variável `ANTHROPIC_MODEL`).

## Atualizar os dados

Depois de rodar `./executar_nacional.sh` na pasta do projeto, copie o conteúdo de `painel/`
(`brasil.csv`, `brasil_ufs.csv`, `municipios.csv`, `uf/`) para `webapp/dados/` e publique de novo
(`npx vercel --prod`).
