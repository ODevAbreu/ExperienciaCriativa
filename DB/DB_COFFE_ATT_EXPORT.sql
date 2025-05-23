DROP DATABASE IF EXISTS coffee;
CREATE DATABASE coffee;
USE coffee;

-- Tabela usuario
CREATE TABLE usuario (
  Id INT AUTO_INCREMENT PRIMARY KEY,
  Nome VARCHAR(100),
  Email VARCHAR(50),
  Senha VARCHAR(100),
  Dt_Nasc DATE,
  Telefone VARCHAR(20),
  CPF VARCHAR(20) UNIQUE,
  ADM TINYINT(1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela endereco
CREATE TABLE endereco (
  ID_Endereco INT AUTO_INCREMENT PRIMARY KEY,
  Rua VARCHAR(100),
  Numero VARCHAR(10),
  Cidade VARCHAR(50),
  CEP VARCHAR(20),
  Bairro VARCHAR(50),
  fk_ID_Usuario INT,
  FOREIGN KEY (fk_ID_Usuario) REFERENCES usuario(Id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela compra
CREATE TABLE compra (
  ID_Compra INT AUTO_INCREMENT PRIMARY KEY,
  ID_Usuario INT,
  ID_Endereco INT,
  Status VARCHAR(20) DEFAULT 'aberta',
  FOREIGN KEY (ID_Usuario) REFERENCES usuario(Id) ON DELETE CASCADE,
  FOREIGN KEY (ID_Endereco) REFERENCES endereco(ID_Endereco) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela produto
CREATE TABLE produto (
  ID_Produto INT AUTO_INCREMENT PRIMARY KEY,
  Nome_Produto VARCHAR(50),
  Descr_Produto VARCHAR(500),
  Preco_prod FLOAT,
  Tipo_prod VARCHAR(50),
  Qtn_Produto INT,
  Img_Produto LONGBLOB
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela qtd_produto
CREATE TABLE qtd_produto (
  fk_Compra_ID_Compra INT,
  fk_Produto_ID_Produto INT,
  Qtn_Produto INT,
  FOREIGN KEY (fk_Compra_ID_Compra) REFERENCES compra(ID_Compra) ON DELETE CASCADE,
  FOREIGN KEY (fk_Produto_ID_Produto) REFERENCES produto(ID_Produto) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Inserir usuário administrador
INSERT INTO usuario (
  Id, Nome, Email, Senha, Dt_Nasc, Telefone, CPF, ADM
) VALUES (
  1, 'Administrador', 'adm@coffee.com',
  '$2b$12$c0yaoS7wZD6VO90bvZo4ROfGOexHXQhYe7a9YtPD5opeN1rUOnkDq',
  '2005-05-06', '(41) 99978-1028', '45149549002', 1
);
/* SENHA DO ADM: ADM@1234 */
