import database from "../../../infra/database";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { serialize } from "cookie";

const secret = process.env.SECRET;

async function login(req, res) {
  // define headers cors
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, PUT, DELETE, OPTIONS",
  );
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (!req.method === "POST") {
    res.status(405).end();
    return;
  }
  const { email, password } = req.body;

  const getUserQuery = `
    SELECT id, email, password
    FROM users
    WHERE email = '${email}';
  `;

  const result = await database.query(getUserQuery);
  const user = result.rows[0];

  if (!user) {
    res.status(401).json({ message: "Usuário não encontrado" });
    return;
  }

  const isValid = bcrypt.compareSync(password, user.password);
  if (!isValid) {
    res.status(401).json({ message: "Senha inválida" });
    return;
  }

  const token = jwt.sign({ id: user.id, email: user.email }, secret, {
    expiresIn: "7d",
  });

  res.setHeader(
    "Set-Cookie",
    serialize("session", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
    }),
  );
  res.status(200).json({ message: "Login realizado com sucesso" });
}

export default login;
