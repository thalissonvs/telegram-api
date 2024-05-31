import database from "../../../infra/database";

async function payments(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, OPTIONS",
  );
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  console.log(req.method);

  const methodsMap = {
    GET: getPayments,
    POST: postPayment,
  };

  if (methodsMap[req.method]) {
    return methodsMap[req.method](req, res);
  } else {
    res.status(405).json({ error: "Method not allowed" });
  }
}

async function getPayments(req, res) {
  const client_id = req.query.client_id;

  // faz um join com a tabela de clientes para trazer o nome do cliente
  if (!client_id) {
    res.status(400).json({ error: "Missing client_id" });
  }

  const getPaymentQuery = `
    SELECT p.id, p.client_id, c.first_name, p.price, p.mercado_pago_id, p.date
    FROM payments p
    JOIN clients c ON p.client_id = c.id
    WHERE p.client_id = ${client_id};
  `;

  const result = await database.query(getPaymentQuery);
  const payments = result.rows;
  res.status(200).json(payments);
}

async function postPayment(req, res) {
  const client_id = req.body.client_id;
  const price = req.body.price;
  const mercado_pago_id = req.body.mercado_pago_id;

  if (!client_id || !price || !mercado_pago_id) {
    res.status(400).json({ error: "Missing fields" });
    return;
  }

  const postPaymentQuery = `
    INSERT INTO payments (client_id, price, mercado_pago_id)
    VALUES (${client_id}, ${price}, '${mercado_pago_id}');
  `;

  try {
    await database.query(postPaymentQuery);
    res.status(200).json({ status: "ok" });
  } catch (err) {
    console.error("Error posting payment", err);
    res.status(500).json({ error: "Internal server error" });
  }
}

export default payments;
