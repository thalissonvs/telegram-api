import { NextResponse } from "next/server";

export async function middleware(request) {
  const session = request.cookies.get("session");

  if (!session) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  const token = session.value;

  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  const response = await fetch(new URL("/api/v1/verifyToken", request.url), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ token }),
  });

  if (response.status === 200) {
    return NextResponse.next();
  } else {
    return NextResponse.redirect(new URL("/login", request.url));
  }
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: ["/quizzes", "/api/v1/quizzes"],
};
