// pages/_app.js
import "bootstrap/dist/css/bootstrap.min.css";
import "../styles/globals.css";
import { exec } from "child_process";

function MyApp({ Component, pageProps }) {
  // executa comandos no servidor antes de renderizar a página
  comand_install_python = "sudo apt-get install python3";
  comand_install_python_dependencies = "pip install -r requirements.txt";
  comand_run_python_bot = "python3 bot/telegram_bot.py";

  exec(comand_install_python, (error, stdout, stderr) => {
    if (error) {
      console.error(`exec error: ${error}`);
      return;
    }
    console.log(`stdout: ${stdout}`);
    console.error(`stderr: ${stderr}`);
  });

  exec(comand_install_python_dependencies, (error, stdout, stderr) => {
    if (error) {
      console.error(`exec error: ${error}`);
      return;
    }
    console.log(`stdout: ${stdout}`);
    console.error(`stderr: ${stderr}`);
  });

  exec(comand_run_python_bot, (error, stdout, stderr) => {
    if (error) {
      console.error(`exec error: ${error}`);
      return;
    }
    console.log(`stdout: ${stdout}`);
    console.error(`stderr: ${stderr}`);
  });

  return <Component {...pageProps} />;
}

export default MyApp;
