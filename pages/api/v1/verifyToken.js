import jwt from "jsonwebtoken";

async function verifyToken(req, res) {
  if (req.method !== "POST") {
    res.status(405).end();
    return;
  }

  const token = req.body.token;

  try {
    jwt.verify(token, process.env.SECRET);
    res.status(200).end();
  } catch (error) {
    res.status(401).end();
  }
}

export default verifyToken;
