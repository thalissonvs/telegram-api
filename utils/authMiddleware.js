import jwt, { TokenExpiredError } from "jsonwebtoken";
import { parse } from "cookie";

const secret = process.env.SECRET;

export function requireAuth(req, res) {
  const { session } = parse(req.headers.cookie || "");

  if (!session) {
    return null;
  }

  try {
    const decoded = jwt.verify(session, secret);
    req.user = { id: decoded.id, email: decoded.email, token: session };
    return { props: { user: req.user } };
  } catch (err) {
    return null;
  }
}
