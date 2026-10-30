// Função do servidor (Vercel): repassa as perguntas do chat para a API da Anthropic.
// A chave fica só aqui, na variável de ambiente ANTHROPIC_API_KEY; nunca vai para o navegador.
// Variáveis: ANTHROPIC_API_KEY (obrigatória), CODIGO_ACESSO (opcional, recomendado),
//            ANTHROPIC_MODEL (opcional; padrão claude-sonnet-5-5).

const FERRAMENTAS = new Set(['consultar_indicadores', 'residencia_pacientes', 'listar_valores']);

export default async function handler(req, res) {
  const KEY = process.env.ANTHROPIC_API_KEY || '';
  const COD = process.env.CODIGO_ACESSO || '';
  const MODELO = process.env.ANTHROPIC_MODEL || 'claude-sonnet-5-5';

  if (req.method === 'GET') return res.status(200).json({ configurado: !!KEY, precisa_codigo: !!COD });
  if (req.method !== 'POST') return res.status(405).json({ erro: 'Método não permitido.' });
  if (!KEY) return res.status(503).json({ erro: 'Chave da API não configurada.' });
  if (COD && req.headers['x-codigo-acesso'] !== COD) return res.status(401).json({ erro: 'Código de acesso inválido.' });

  let b = req.body;
  try { if (typeof b === 'string') b = JSON.parse(b); } catch { return res.status(400).json({ erro: 'Pedido inválido.' }); }
  if (!b || typeof b.system !== 'string' || !Array.isArray(b.messages) || !Array.isArray(b.tools)) return res.status(400).json({ erro: 'Pedido inválido.' });
  if (JSON.stringify(b).length > 250000 || b.messages.length > 40) return res.status(413).json({ erro: 'Conversa longa demais.' });
  if (b.system.length > 8000 || b.tools.length > 5 || !b.tools.every((t) => FERRAMENTAS.has(t?.name))) return res.status(400).json({ erro: 'Pedido inválido.' });

  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      body: JSON.stringify({ model: MODELO, max_tokens: 2048, system: b.system, messages: b.messages, tools: b.tools }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) return res.status(r.status === 429 ? 429 : 502).json({ erro: j?.error?.message || 'Falha na API da Anthropic.' });
    return res.status(200).json({ content: j.content, stop_reason: j.stop_reason });
  } catch (e) {
    return res.status(502).json({ erro: 'Não foi possível falar com a API da Anthropic.' });
  }
}
