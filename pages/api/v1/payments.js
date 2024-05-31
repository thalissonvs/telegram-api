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

  const getPaymentQuery = `
    SELECT id, client_id, price, mercado_pago_id, date
    FROM payments
    WHERE client_id = ${client_id};
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
