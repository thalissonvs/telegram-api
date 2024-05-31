import database from "../../../infra/database";

async function prizes(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, OPTIONS",
  );
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  console.log(req.method);

  const methodsMap = {
    GET: getPrizes,
    POST: postPrize,
    PUT: updatePrize,
  };

  if (methodsMap[req.method]) {
    return methodsMap[req.method](req, res);
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
}

async function getPrizes(req, res) {
  const client_id = req.query.client_id;

  // faz um join com a tabela de clientes para trazer o nome do cliente
  if (!client_id) {
    res.status(400).json({ error: "Missing client_id" });
  }

  const getPrizesQuery = `
    SELECT p.id, p.client_id, c.first_name, p.price, p.status
    FROM prizes p
    JOIN clients c ON p.client_id = c.id
    WHERE p.client_id = ${client_id};
  `;

  const result = await database.query(getPrizesQuery);
  const prizes = result.rows;
  res.status(200).json(prizes);
}

async function postPrize(req, res) {
  const client_id = req.body.client_id;
  const price = req.body.price;
  const status = req.body.status;

  if (!client_id || !price || !status) {
    res.status(400).json({ error: "Missing fields" });
    return;
  }

  const postPrizeQuery = `
    INSERT INTO prizes (client_id, price, status)
    VALUES (${client_id}, ${price}, ${status});
  `;

  try {
    await database.query(postPrizeQuery);
    res.status(200).json({ status: "ok" });
  } catch (err) {
    console.error("Error posting prize", err);
    res.status(500).json({ error: "Internal server error" });
  }
}

async function updatePrize(req, res) {
  const id = req.body.id;
  const status = req.body.status;

  if (!id || !status) {
    res.status(400).json({ error: "Missing fields" });
    return;
  }

  const updatePrizeQuery = `
    UPDATE prizes
    SET status = ${status}
    WHERE id = ${id};
  `;

  try {
    await database.query(updatePrizeQuery);
    res.status(200).json({ status: "ok" });
  } catch (err) {
    console.error("Error updating prize", err);
    res.status(500).json({ error: "Internal server error" });
  }
}

export default prizes;
