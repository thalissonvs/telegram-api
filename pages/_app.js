// pages/_app.js
import "bootstrap/dist/css/bootstrap.min.css";
import "../styles/globals.css";
import { exec } from "child_process";

function MyApp({ Component, pageProps }) {
  // executa comandos no servidor antes de renderizar a página
  return <Component {...pageProps} />;
}

export default MyApp;
