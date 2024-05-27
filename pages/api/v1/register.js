import database from "../../../infra/database";
import bcrypt from "bcryptjs";

async function register(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*"); // Permitir todas as origens
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, OPTIONS",
  ); // Métodos permitidos
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization"); // Cabeçalhos permitidos

  const methodsMap = {
    POST: postUser,
  };

  if (methodsMap[req.method]) {
    return methodsMap[req.method](req, res);
  } else {
    res.status(405).end();
  }
}

async function postUser(req, res) {
  const { email, password } = req.body;

  const hash = bcrypt.hashSync(password, 10);
  const postUserQuery = `
    INSERT INTO users (email, password)
    VALUES ('${email}', '${hash}')
    RETURNING id;
  `;
  const result = await database.query(postUserQuery);
  const userId = result.rows[0].id;

  res.status(201).json({ userId });
}

export default register;
