// pages/_app.js
import "bootstrap/dist/css/bootstrap.min.css";

function MyApp({ Component, pageProps }) {
  // executa comandos no servidor antes de renderizar a página
  // insere o js do bootstrap no final do body
  return (
    <>
      <Component {...pageProps} />
    </>
  );
}

export default MyApp;
