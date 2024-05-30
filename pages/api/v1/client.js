import database from "../../../infra/database";

async function client(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, OPTIONS",
  );
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  const methodsMap = {
    DELETE: deleteClient,
    GET: getClient,
    POST: postClient,
    PUT: updateClient,
  };

  if (methodsMap[req.method]) {
    return methodsMap[req.method](req, res);
  } else {
    res.status(405).end();
  }
}

async function getClient(req, res) {
  const chat_id = req.query.chat_id;

  const getClientQuery = `
    SELECT id, first_name, email, chat_id, pix_type, pix_key, balance
    FROM clients
    WHERE chat_id = '${chat_id}';
  `;

  const result = await database.query(getClientQuery);
  const client = result.rows;
  res.status(200).json(client);
}

async function postClient(req, res) {
  const first_name = req.body.first_name;
  const email = req.body.email;
  const chat_id = req.body.chat_id;
  const pix_type = req.body.pix_type;
  const pix_key = req.body.pix_key;
  const balance = 0;

  // valida se os dados não são nulos
  if (!first_name || !email || !chat_id || !pix_type || !pix_key) {
    res.status(400).json({ error: "Missing fields" });
    return;
  }

  // verifica se o cliente já existe
  const clientExistsResponse = await database.query(`
    SELECT email
    FROM clients
    WHERE email = '${email}';
  `);
  const clientExists = clientExistsResponse.rowCount > 0;

  if (clientExists) {
    res.status(400).json({ error: "Client already exists" });
    return;
  }

  const validTypes = ["CPF", "CNPJ", "Chave aleatória", "Email", "Telefone"];
  if (!validTypes.includes(pix_type)) {
    res.status(400).json({ error: "Invalid pix_type" });
    return;
  }

  const postClientQuery = `
    INSERT INTO clients (first_name, email, chat_id, pix_type, pix_key, balance)
    VALUES ('${first_name}', '${email}', ${chat_id}, '${pix_type}', '${pix_key}', ${balance})
    RETURNING id;
  `;

  const result = await database.query(postClientQuery);
  const clientId = result.rows[0].id;
  res.status(200).json({ id: clientId });
}

async function deleteClient(req, res) {
  const email = req.body.email;
  const deleteClientQuery = `
    DELETE FROM clients
    WHERE email = '${email}';
  `;
  await database.query(deleteClientQuery);
  res.status(200).end();
}

async function updateClient(req, res) {
  const email = req.body.email;
  const balance = req.body.balance;
  const pix_type = req.body.pix_type;
  const pix_key = req.body.pix_key;

  const updateClientQuery = `
    UPDATE clients
    SET balance = ${balance}, pix_type = '${pix_type}', pix_key = '${pix_key}'
    WHERE email = '${email}';
  `;
  await database.query(updateClientQuery);
  res.status(200).end();
}

export default client;
