import { MercadoPagoConfig, Payment } from "mercadopago";
import { v4 as uuidv4 } from "uuid";

async function getPayment(req, res) {
  const paymentId = req.query.id;
  const accessToken = req.query.accessToken;

  const client = new MercadoPagoConfig({
    accessToken: accessToken,
  });
  const payment = new Payment(client);
  const idempotencyKey = uuidv4();
  const requestOptions = {
    idempotencyKey: idempotencyKey,
  };

  try {
    const response = await payment.get({
      id: paymentId,
      requestOptions: requestOptions,
    });
    res.status(200).json({ status: response.status });
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: error.message });
  }
}

export default getPayment;
