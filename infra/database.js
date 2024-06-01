import { Client } from "pg";

function getClient() {
  return new Client({
    user: process.env.POSTGRES_USER,
    host: process.env.POSTGRES_HOST,
    database: process.env.POSTGRES_DB,
    password: process.env.POSTGRES_PASSWORD,
    port: process.env.POSTGRES_PORT,
    ssl: process.env.NODE_ENV === "production",
  });
}

async function query(queryObject) {
  checkTables();
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
      id SERIAL PRIMARY KEY,
      price INTEGER NOT NULL,
      difficulty INTEGER NOT NULL
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

async function createTableClients() {
  const client = getClient();
  await client.connect();

  const createTableClients = `
    CREATE TABLE clients (
      id SERIAL PRIMARY KEY,
      first_name VARCHAR(255) NOT NULL,
      email VARCHAR(255) NOT NULL,
      chat_id INTEGER NOT NULL,
      pix_type VARCHAR(255) NOT NULL,
      pix_key VARCHAR(255) NOT NULL,
      balance FLOAT NOT NULL
    );
  `;

  try {
    await client.query(createTableClients);
    console.log("Table clients created successfully");
  } catch (err) {
    console.error("Error creating table clients", err);
  } finally {
    await client.end();
  }
}

async function createTablePayments() {
  const client = getClient();
  await client.connect();

  const createTablePayments = `
    CREATE TABLE payments (
      id SERIAL PRIMARY KEY,
      client_id INTEGER NOT NULL,
      price FLOAT NOT NULL,
      mercado_pago_id VARCHAR(255),
      date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (client_id) REFERENCES clients(id)
    )
  `;

  try {
    await client.query(createTablePayments);
    console.log("Table payments created successfully");
  } catch (err) {
    console.error("Error creating table payments", err);
  } finally {
    await client.end();
  }
}

async function createTablePrizes() {
  const client = getClient();
  await client.connect();

  const createTablePrizes = `
    CREATE TABLE prizes (
      id SERIAL PRIMARY KEY,
      client_id INTEGER NOT NULL,
      price FLOAT NOT NULL,
      status INTEGER NOT NULL,
      date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (client_id) REFERENCES clients(id)
    )
  `;

  try {
    await client.query(createTablePrizes);
    console.log("Table prizes created successfully");
  } catch (err) {
    console.error("Error creating table prizes", err);
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

  const checkTableClients = `
    SELECT to_regclass('public.clients') as table_name;
  `;

  const checkTablePayments = `
    SELECT to_regclass('public.payments') as table_name;
  `;

  const checkTablePrizes = `
    SELECT to_regclass('public.prizes') as table_name;
  `;

  try {
    const resultQuizzes = await client.query(checkTableQuizzes);
    const resultOptions = await client.query(checkTableOptions);
    const resultPrices = await client.query(checkTablePrices);
    const resultUsers = await client.query(checkTableUsers);
    const resultClients = await client.query(checkTableClients);
    const resultPayments = await client.query(checkTablePayments);
    const resultPrizes = await client.query(checkTablePrizes);

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

    if (!resultClients.rows[0].table_name) {
      await createTableClients();
    }

    if (!resultPayments.rows[0].table_name) {
      await createTablePayments();
    }

    if (!resultPrizes.rows[0].table_name) {
      await createTablePrizes();
    }

    console.log("Tables checked successfully");
  } catch (err) {
    console.error("Error checking tables", err);
  } finally {
    await client.end();
  }
}

export default {
  query: query,
};
