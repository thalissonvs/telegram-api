import { Client } from "pg";

function getClient() {
  return new Client({
    user: process.env.POSTGRES_USER,
    host: process.env.POSTGRES_HOST,
    database: process.env.POSTGRES_DB,
    password: process.env.POSTGRES_PASSWORD,
    port: process.env.POSTGRES_PORT,
  });
}

async function query(queryObject) {
  const client = getClient();
  await client.connect();
  const result = await client.query(queryObject);
  await client.end();
  return result;
}

async function createTableQuizzes() {
  const client = getClient();
  await client.connect();

  const createTableQuizzes = `
    CREATE TABLE quizzes (
      id SERIAL PRIMARY KEY,
      question VARCHAR(255) NOT NULL,
      difficulty INTEGER NOT NULL
    );
  `;

  try {
    await client.query(createTableQuizzes);
    console.log("Table quizzes created successfully");
  } catch (err) {
    console.error("Error creating table quizzes", err);
  } finally {
    await client.end();
  }
}

async function createTableOptions() {
  const client = getClient();
  await client.connect();

  const createTableOptions = `
    CREATE TABLE options (
      id SERIAL PRIMARY KEY,
      quiz_id INTEGER NOT NULL,
      option_label CHAR(1) NOT NULL,
      option_text VARCHAR(255) NOT NULL,
      is_correct BOOLEAN NOT NULL,
      FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
    );
  `;

  try {
    await client.query(createTableOptions);
    console.log("Table options created successfully");
  } catch (err) {
    console.error("Error creating table options", err);
  } finally {
    await client.end();
  }
}

async function createTablePrices() {
  const client = getClient();
  await client.connect();

  const createTablePrices = `
    CREATE TABLE prices (
      difficulty INTEGER PRIMARY KEY,
      price INTEGER NOT NULL
    );
  `;

  try {
    await client.query(createTablePrices);
    console.log("Table prices created successfully");
  } catch (err) {
    console.error("Error creating table prices", err);
  } finally {
    await client.end();
  }
}

async function createTableUsers() {
  const client = getClient();
  await client.connect();

  const createTableUsers = `
    CREATE TABLE users (
      id SERIAL PRIMARY KEY,
      email VARCHAR(255) NOT NULL,
      password VARCHAR(255) NOT NULL
    );
  `;

  try {
    await client.query(createTableUsers);
    console.log("Table users created successfully");
  } catch (err) {
    console.error("Error creating table users", err);
  } finally {
    await client.end();
  }
}

// verifica se as tabelas já existem, se não, chama o método para criar
async function checkTables() {
  const client = getClient();
  await client.connect();

  const checkTableQuizzes = `
    SELECT to_regclass('public.quizzes') as table_name;
  `;

  const checkTableOptions = `
    SELECT to_regclass('public.options') as table_name;
  `;

  const checkTablePrices = `
    SELECT to_regclass('public.prices') as table_name;
  `;

  const checkTableUsers = `
    SELECT to_regclass('public.users') as table_name;
  `;

  try {
    const resultQuizzes = await client.query(checkTableQuizzes);
    const resultOptions = await client.query(checkTableOptions);
    const resultPrices = await client.query(checkTablePrices);
    const resultUsers = await client.query(checkTableUsers);

    if (!resultQuizzes.rows[0].table_name) {
      await createTableQuizzes();
    }

    if (!resultOptions.rows[0].table_name) {
      await createTableOptions();
    }

    if (!resultPrices.rows[0].table_name) {
      await createTablePrices();
    }

    if (!resultUsers.rows[0].table_name) {
      await createTableUsers();
    }

    console.log("Tables checked successfully");
  } catch (err) {
    console.error("Error checking tables", err);
  } finally {
    await client.end();
  }
}

checkTables();

export default {
  query: query,
};
