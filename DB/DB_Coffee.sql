/* Lógico_1: */
DROP DATABASE IF EXISTS coffee;
CREATE DATABASE coffee;
USE coffee;

CREATE TABLE Usuario (
    Id int PRIMARY KEY AUTO_INCREMENT,
    Nome VARCHAR(100),
    Email VARCHAR(50),
    Senha VARCHAR(100),
    Dt_Nasc Date,
    Telefone VARCHAR(20),
    CPF VARCHAR(20) UNIQUE,
    ADM BOOLEAN
);
INSERT INTO `usuario` VALUES (1,'Administrador','adm@coffee.com','$2b$12$c0yaoS7wZD6VO90bvZo4ROfGOexHXQhYe7a9YtPD5opeN1rUOnkDq','2025-05-06','(10) 29478-10281','45149549002',1);
/*SENHA DO ADM : ADM@1234*/;
CREATE TABLE Compra (
    ID_Compra INT PRIMARY KEY,
    ID_Usuario INT
);

CREATE TABLE Produto (
    ID_Produto INT PRIMARY KEY auto_increment,
    Nome_Produto VARCHAR(50),
    Descr_Produto VARCHAR(500),
    Preco_prod FLOAT,
    Tipo_prod VARCHAR(50),
    Qtn_Produto INT
);

CREATE TABLE QTD_Produto (
    fk_Compra_ID_Compra INT,
    fk_Produto_ID_Produto INT,
    Qtn_Produto INT
);
 
ALTER TABLE QTD_Produto ADD CONSTRAINT FK_QTD_Produto_1
    FOREIGN KEY (fk_Compra_ID_Compra)
    REFERENCES Compra (ID_Compra)
    ON DELETE CASCADE;
 
ALTER TABLE QTD_Produto ADD CONSTRAINT FK_QTD_Produto_2
    FOREIGN KEY (fk_Produto_ID_Produto)
    REFERENCES Produto (ID_Produto)
    ON DELETE CASCADE;

ALTER TABLE COMPRA ADD CONSTRAINT FK_COMPRA_1 
    FOREIGN KEY(ID_Usuario)
    REFERENCES Usuario(Id);
    ON DELETE CASCADE

