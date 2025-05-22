CREATE DATABASE IF NOT EXISTS `coffee` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `coffee`;

-- Tabela compra
DROP TABLE IF EXISTS `compra`;
CREATE TABLE `compra` (
  `ID_Compra` int(11) NOT NULL AUTO_INCREMENT,
  `ID_Usuario` int(11) DEFAULT NULL,
  `ID_Endereco` int(11) DEFAULT NULL,
  `Status` varchar(20) DEFAULT 'aberta',
  PRIMARY KEY (`ID_Compra`),
  KEY `FK_COMPRA_1` (`ID_Usuario`),
  CONSTRAINT `FK_COMPRA_1` FOREIGN KEY (`ID_Usuario`) REFERENCES `usuario` (`Id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela endereco (alterada para referenciar ID_Usuario)
DROP TABLE IF EXISTS `endereco`;
CREATE TABLE `endereco` (
  `ID_Endereco` int(11) NOT NULL AUTO_INCREMENT,
  `Rua` varchar(100) DEFAULT NULL,
  `Numero` varchar(10) DEFAULT NULL,
  `Cidade` varchar(50) DEFAULT NULL,
  `CEP` varchar(20) DEFAULT NULL,
  `fk_ID_Usuario` int(11) DEFAULT NULL,  -- Alterado para fk_ID_Usuario
  `Bairro` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`ID_Endereco`),
  KEY `FK_Endereco_Usuario` (`fk_ID_Usuario`),  -- Alterado para FK_Endereco_Usuario
  CONSTRAINT `FK_Endereco_Usuario` FOREIGN KEY (`fk_ID_Usuario`) REFERENCES `usuario` (`Id`) ON DELETE CASCADE  -- Alterado para referenciar a tabela usuario
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela produto
DROP TABLE IF EXISTS `produto`;
CREATE TABLE `produto` (
  `ID_Produto` int(11) NOT NULL AUTO_INCREMENT,
  `Nome_Produto` varchar(50) DEFAULT NULL,
  `Descr_Produto` varchar(500) DEFAULT NULL,
  `Preco_prod` float DEFAULT NULL,
  `Tipo_prod` varchar(50) DEFAULT NULL,
  `Qtn_Produto` int(11) DEFAULT NULL,
  `Img_Produto` longblob DEFAULT NULL,
  PRIMARY KEY (`ID_Produto`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela qtd_produto
DROP TABLE IF EXISTS `qtd_produto`;
CREATE TABLE `qtd_produto` (
  `fk_Compra_ID_Compra` int(11) DEFAULT NULL,
  `fk_Produto_ID_Produto` int(11) DEFAULT NULL,
  `Qtn_Produto` int(11) DEFAULT NULL,
  KEY `FK_QTD_Produto_1` (`fk_Compra_ID_Compra`),
  KEY `FK_QTD_Produto_2` (`fk_Produto_ID_Produto`),
  CONSTRAINT `FK_QTD_Produto_1` FOREIGN KEY (`fk_Compra_ID_Compra`) REFERENCES `compra` (`ID_Compra`) ON DELETE CASCADE,
  CONSTRAINT `FK_QTD_Produto_2` FOREIGN KEY (`fk_Produto_ID_Produto`) REFERENCES `produto` (`ID_Produto`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Tabela usuario
DROP TABLE IF EXISTS `usuario`;
CREATE TABLE `usuario` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `Nome` varchar(100) DEFAULT NULL,
  `Email` varchar(50) DEFAULT NULL,
  `Senha` varchar(100) DEFAULT NULL,
  `Dt_Nasc` date DEFAULT NULL,
  `Telefone` varchar(20) DEFAULT NULL,
  `CPF` varchar(20) DEFAULT NULL,
  `ADM` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `CPF` (`CPF`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `usuario` VALUES (1,'Administrador','adm@coffee.com','$2b$12$c0yaoS7wZD6VO90bvZo4ROfGOexHXQhYe7a9YtPD5opeN1rUOnkDq','2025-05-06','(10) 29478-10281','45149549002',1);
/*SENHA DO ADM : ADM@1234*/;