import jwt from "jsonwebtoken";

async function verifyLogin(req, res) {
  const token = req.cookies.session;

  try {
    jwt.verify(token, process.env.SECRET);
    res.status(200).end();
  } catch (error) {
    res.status(401).end();
  }
}

export default verifyLogin;
