import database from "../../../infra/database";

async function notifyPayment(req, res) {
  const price = req.body.price;
  const chat_id = req.body.chat_id;
  const prize_id = req.body.id;

  const textToSend =
    "Boas notícias! Seu prêmio no valor de R$ " +
    price +
    " foi pago com sucesso!";
  const key = process.env.TELEGRAM_KEY;

  const url = `https://api.telegram.org/bot${key}/sendMessage?chat_id=${chat_id}&text=${textToSend}`;
  await fetch(url);

  const updatePrizeQuery = `
    UPDATE prizes
    SET status = 1
    WHERE id = ${prize_id};
  `;

  try {
    await database.query(updatePrizeQuery);
    res.status(200).json({ status: "ok" });
  } catch (err) {
    console.error("Error updating prize", err);
    res.status(500).json({ error: "Internal server error" });
  }
}

export default notifyPayment;
