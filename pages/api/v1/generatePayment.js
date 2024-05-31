import { MercadoPagoConfig, Payment } from "mercadopago";
import { v4 as uuidv4 } from "uuid";

async function generatePayment(req, res) {
  const price = req.body.price;
  const email = req.body.email;
  const accessToken = req.body.accessToken;

  const client = new MercadoPagoConfig({
    accessToken: accessToken,
  });
  const payment = new Payment(client);

  const body = {
    transaction_amount: parseFloat(price),
    description: "Adição de créditos",
    payment_method_id: "pix",
    payer: {
      email: email,
    },
  };

  const idempotencyKey = uuidv4();

  const requestOptions = {
    idempotencyKey: idempotencyKey,
  };

  try {
    const response = await payment.create({ body, requestOptions });

    res.status(200).json({
      id: response.id,
      qr_code_base64:
        response.point_of_interaction.transaction_data.qr_code_base64,
      qr_code: response.point_of_interaction.transaction_data.qr_code,
    });
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: error.message });
  }
}

export default generatePayment;
