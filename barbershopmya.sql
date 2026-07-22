-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 22-07-2026 a las 17:20:13
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `barbershopmya`
--

DELIMITER $$
--
-- Procedimientos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `ActualizarTelefonoUsuario` (`pId` INT, `pNuevoCel` VARCHAR(15))   BEGIN
    UPDATE Usuario SET numCelular = pNuevoCel WHERE idUsuario = pId;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `EliminarPagoPendiente` (`pId` INT)   BEGIN
    DELETE FROM Pago WHERE idPago = pId AND estadoPago = 'PENDIENTE';
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `HistorialCitaPorCliente` (IN `pIdCliente` INT)   BEGIN
    SELECT c.idCita, u.nombre AS Cliente, c.fecha, c.horaInicio, s.nombreServicio, c.observaciones
    FROM Cita c
    INNER JOIN Cliente cl ON c.idClienteFk = cl.idCliente
    INNER JOIN Usuario u ON cl.idUsuarioFk = u.idUsuario
    INNER JOIN Servicio s ON c.idServicioFk = s.idServicio 
    WHERE cl.idCliente = pIdCliente
    ORDER BY c.fecha DESC, c.horaInicio DESC;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `RegistrarCitaCompleta` (IN `p_idBarbero` INT, IN `p_idCliente` INT, IN `p_idServicio` INT, IN `p_fecha` DATE, IN `p_hora` TIME, IN `p_idPago` INT)   BEGIN
    DECLARE v_idAgenda INT;

    -- 1. Insertamos primero en Agenda
    INSERT INTO agenda (idBarberoFk, fecha, horaInicio) 
    VALUES (p_idBarbero, p_fecha, p_hora);
    
    -- 2. Obtenemos el ID generado
    SET v_idAgenda = LAST_INSERT_ID();
    
    -- 3. Insertamos en Cita usando el ID de la agenda
    INSERT INTO cita (idBarberoFk, idClienteFk, idServicioFk, idAgendaFk, fecha, horaInicio, idPagoFk)
    VALUES (p_idBarbero, p_idCliente, p_idServicio, v_idAgenda, p_fecha, p_hora, p_idPago);
    
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `RegistrarServicioExpress` (`pNom` VARCHAR(60), `pPrecio` DECIMAL(10,2))   BEGIN
    INSERT INTO Servicio (nombreServicio, duracion, precio, tipoServicio) 
    VALUES (pNom, 30, pPrecio, 'Express');
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `VerCitasHoy` ()   BEGIN
    SELECT c.idCita, u.nombre AS nombreCliente, s.nombreServicio, c.horaInicio, bu.nombre AS nombreBarbero
    FROM Cita c
    INNER JOIN Cliente cl ON c.idClienteFk = cl.idCliente
    INNER JOIN Usuario u ON cl.idUsuarioFk = u.idUsuario
    INNER JOIN Servicio s ON c.idServicioFk = s.idServicio
    INNER JOIN Barbero b ON c.idBarberoFk = b.idBarbero
    INNER JOIN Usuario bu ON b.idUsuarioFk = bu.idUsuario;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `agenda`
--

CREATE TABLE `agenda` (
  `idAgenda` int(11) NOT NULL,
  `idBarberoFk` int(11) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `horaInicio` time DEFAULT NULL,
  `horaFin` time DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `agenda`
--

INSERT INTO `agenda` (`idAgenda`, `idBarberoFk`, `fecha`, `horaInicio`, `horaFin`) VALUES
(1, 1, '2026-03-20', '09:00:00', '13:00:00'),
(3, 1, '2026-03-21', '09:00:00', '13:00:00'),
(4, 2, '2026-03-21', '15:00:00', '19:00:00'),
(5, 1, '2026-03-22', '09:00:00', '13:00:00'),
(6, 2, '2026-03-22', '10:00:00', '14:00:00'),
(7, 1, '2026-03-23', '09:00:00', '13:00:00'),
(9, 1, '2026-03-24', '09:00:00', '13:00:00'),
(10, 2, '2026-03-24', '10:00:00', '14:00:00'),
(11, 11, '2026-06-24', '08:00:00', NULL),
(12, 11, '2026-06-25', '09:00:00', NULL),
(14, 11, '2026-06-30', '08:00:00', NULL),
(25, 11, '2026-07-02', '08:00:00', NULL),
(26, 11, '2026-07-02', '09:00:00', NULL),
(28, 11, '2026-07-09', '08:00:00', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add rol', 7, 'add_rol'),
(26, 'Can change rol', 7, 'change_rol'),
(27, 'Can delete rol', 7, 'delete_rol'),
(28, 'Can view rol', 7, 'view_rol'),
(29, 'Can add usuario', 8, 'add_usuario'),
(30, 'Can change usuario', 8, 'change_usuario'),
(31, 'Can delete usuario', 8, 'delete_usuario'),
(32, 'Can view usuario', 8, 'view_usuario'),
(33, 'Can add agenda', 9, 'add_agenda'),
(34, 'Can change agenda', 9, 'change_agenda'),
(35, 'Can delete agenda', 9, 'delete_agenda'),
(36, 'Can view agenda', 9, 'view_agenda'),
(37, 'Can add barbero', 10, 'add_barbero'),
(38, 'Can change barbero', 10, 'change_barbero'),
(39, 'Can delete barbero', 10, 'delete_barbero'),
(40, 'Can view barbero', 10, 'view_barbero'),
(41, 'Can add cita', 11, 'add_cita'),
(42, 'Can change cita', 11, 'change_cita'),
(43, 'Can delete cita', 11, 'delete_cita'),
(44, 'Can view cita', 11, 'view_cita'),
(45, 'Can add pago', 12, 'add_pago'),
(46, 'Can change pago', 12, 'change_pago'),
(47, 'Can delete pago', 12, 'delete_pago'),
(48, 'Can view pago', 12, 'view_pago'),
(49, 'Can add servicio', 13, 'add_servicio'),
(50, 'Can change servicio', 13, 'change_servicio'),
(51, 'Can delete servicio', 13, 'delete_servicio'),
(52, 'Can view servicio', 13, 'view_servicio'),
(53, 'Can add cita', 14, 'add_cita'),
(54, 'Can change cita', 14, 'change_cita'),
(55, 'Can delete cita', 14, 'delete_cita'),
(56, 'Can view cita', 14, 'view_cita'),
(57, 'Can add configuracion horario', 15, 'add_configuracionhorario'),
(58, 'Can change configuracion horario', 15, 'change_configuracionhorario'),
(59, 'Can delete configuracion horario', 15, 'delete_configuracionhorario'),
(60, 'Can view configuracion horario', 15, 'view_configuracionhorario'),
(61, 'Can add dia habilitado', 16, 'add_diahabilitado'),
(62, 'Can change dia habilitado', 16, 'change_diahabilitado'),
(63, 'Can delete dia habilitado', 16, 'delete_diahabilitado'),
(64, 'Can view dia habilitado', 16, 'view_diahabilitado'),
(65, 'Can add barbero dia habilitado', 17, 'add_barberodiahabilitado'),
(66, 'Can change barbero dia habilitado', 17, 'change_barberodiahabilitado'),
(67, 'Can delete barbero dia habilitado', 17, 'delete_barberodiahabilitado'),
(68, 'Can view barbero dia habilitado', 17, 'view_barberodiahabilitado'),
(69, 'Can add cita', 18, 'add_cita'),
(70, 'Can change cita', 18, 'change_cita'),
(71, 'Can delete cita', 18, 'delete_cita'),
(72, 'Can view cita', 18, 'view_cita'),
(73, 'Can add cliente', 19, 'add_cliente'),
(74, 'Can change cliente', 19, 'change_cliente'),
(75, 'Can delete cliente', 19, 'delete_cliente'),
(76, 'Can view cliente', 19, 'view_cliente'),
(77, 'Can add servicio', 20, 'add_servicio'),
(78, 'Can change servicio', 20, 'change_servicio'),
(79, 'Can delete servicio', 20, 'delete_servicio'),
(80, 'Can view servicio', 20, 'view_servicio'),
(81, 'Can add perfil usuario', 21, 'add_perfilusuario'),
(82, 'Can change perfil usuario', 21, 'change_perfilusuario'),
(83, 'Can delete perfil usuario', 21, 'delete_perfilusuario'),
(84, 'Can view perfil usuario', 21, 'view_perfilusuario'),
(85, 'Can add notificacion', 22, 'add_notificacion'),
(86, 'Can change notificacion', 22, 'change_notificacion'),
(87, 'Can delete notificacion', 22, 'delete_notificacion'),
(88, 'Can view notificacion', 22, 'view_notificacion'),
(89, 'Can add agenda', 23, 'add_agenda'),
(90, 'Can change agenda', 23, 'change_agenda'),
(91, 'Can delete agenda', 23, 'delete_agenda'),
(92, 'Can view agenda', 23, 'view_agenda'),
(93, 'Can add barbero', 24, 'add_barbero'),
(94, 'Can change barbero', 24, 'change_barbero'),
(95, 'Can delete barbero', 24, 'delete_barbero'),
(96, 'Can view barbero', 24, 'view_barbero'),
(97, 'Can add cliente', 25, 'add_cliente'),
(98, 'Can change cliente', 25, 'change_cliente'),
(99, 'Can delete cliente', 25, 'delete_cliente'),
(100, 'Can view cliente', 25, 'view_cliente'),
(101, 'Can add usuario', 26, 'add_usuario'),
(102, 'Can change usuario', 26, 'change_usuario'),
(103, 'Can delete usuario', 26, 'delete_usuario'),
(104, 'Can view usuario', 26, 'view_usuario'),
(105, 'Can add calificacion', 27, 'add_calificacion'),
(106, 'Can change calificacion', 27, 'change_calificacion'),
(107, 'Can delete calificacion', 27, 'delete_calificacion'),
(108, 'Can view calificacion', 27, 'view_calificacion');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_user`
--

CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `auth_user`
--

INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES
(1, 'pbkdf2_sha256$600000$nPIoL97ZaGfrpLKKKn3GZL$7luiGVpO7Eyar3il5EumDiA+Rj1gbKCQJ8qJgF+FeMs=', NULL, 0, 'ivancito@gmail.com', 'Ivan ', 'Cepeda', 'ivancito@gmail.com', 0, 1, '2026-06-18 12:54:47.350764'),
(2, 'pbkdf2_sha256$600000$cOmiRYMYpYxwbGXzoqxcHg$BxVF3vH9nwY4PJxNTWbMhNODYw/kxa2C+UgD1uAMsWw=', '2026-06-18 14:09:14.566411', 0, 'ivan@gmail.com', 'Ivancito', 'Cepeda', 'ivan@gmail.com', 0, 1, '2026-06-18 13:04:14.605021'),
(3, 'pbkdf2_sha256$600000$gJsykzVg87JeL6L7tAxT4p$/yO+vPpJNkbo0ViziEwRZGkHWqbAW5j+8nKGh+SqMmU=', '2026-06-18 13:12:29.381278', 1, 'jimena', '', '', 'jimena@gmail.com', 1, 1, '2026-06-18 13:12:07.378956'),
(4, 'pbkdf2_sha256$600000$HQyAPOsaeV4ROmnxySJedH$ZIhfWy/uWH5wQuBlx0fMsj8PE3yqJ+NTwF+IFlyhNLI=', '2026-07-22 12:29:21.310279', 0, 'derecha@gmail.com', 'James Abelardo', 'Diaz Uribe', 'derecha@gmail.com', 0, 1, '2026-06-18 15:05:47.242567'),
(5, 'pbkdf2_sha256$600000$m6HPb4HxtCJuGyFL53Zkio$ZKD43nyF1vSI5De/JhT+prnMur1yLWocqvDYXQ3lDDU=', '2026-07-02 01:10:44.193504', 0, 'restrepo123@gmail.com', 'Juan Manuel', 'Restrepo', 'restrepo123@gmail.com', 0, 1, '2026-06-22 14:05:23.921634'),
(6, 'pbkdf2_sha256$600000$82sfzCGHimPQKppeCsm30C$eWVhhE4604zJXJhoX0I55EplXFtsEdR8EEh9ZsMVUYI=', '2026-07-22 14:28:04.856462', 0, 'dani@gmail.com', 'dani', 'jordiwilde', 'dani@gmail.com', 0, 1, '2026-06-23 21:06:43.304259'),
(7, 'pbkdf2_sha256$600000$bHYobMHyjKR6Z942ya8elC$xF5a5TWtJQbJzNjXJJU6ahMARJC9sSavvzeU4vs6Ess=', '2026-07-17 14:10:45.193790', 0, 'cliente@gmail.com', 'cliente de prueba', 'uwu', 'cliente@gmail.com', 0, 1, '2026-06-24 20:17:49.165423');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_user_groups`
--

CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_user_user_permissions`
--

CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `barbero`
--

CREATE TABLE `barbero` (
  `idBarbero` int(11) NOT NULL,
  `idUsuarioFk` int(11) DEFAULT NULL,
  `especialidad` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `barbero`
--

INSERT INTO `barbero` (`idBarbero`, `idUsuarioFk`, `especialidad`) VALUES
(1, 2, 'Master Fade'),
(2, 5, 'Barba Clásica'),
(3, 2, 'Cortes Modernos'),
(4, 5, 'Tijera'),
(5, 2, 'Pigmentación'),
(6, 5, 'Tratamientos'),
(7, 2, 'Niños'),
(8, 5, 'Navaja'),
(9, 2, 'Diseño'),
(10, 5, 'Color'),
(11, 17, 'Por asignar'),
(12, 21, 'Por asignar'),
(13, 21, 'Cortes Clásicos'),
(14, 3, 'General'),
(15, 3, 'General');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `barbero_dia_habilitado`
--

CREATE TABLE `barbero_dia_habilitado` (
  `id` bigint(20) NOT NULL,
  `idusuariofk` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `habilitado` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `barbero_dia_habilitado`
--

INSERT INTO `barbero_dia_habilitado` (`id`, `idusuariofk`, `fecha`, `habilitado`) VALUES
(1, 2, '2026-07-31', 1),
(2, 3, '2026-07-31', 1),
(3, 17, '2026-07-31', 1),
(4, 21, '2026-07-31', 1),
(5, 2, '2026-07-23', 1),
(6, 3, '2026-07-23', 1),
(7, 17, '2026-07-23', 1),
(8, 21, '2026-07-23', 1),
(9, 2, '2026-07-25', 1),
(10, 3, '2026-07-25', 1),
(11, 17, '2026-07-25', 1),
(12, 21, '2026-07-25', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `calificacion`
--

CREATE TABLE `calificacion` (
  `idcalificacion` int(11) NOT NULL,
  `calificacion` smallint(5) UNSIGNED NOT NULL CHECK (`calificacion` >= 0),
  `comentario` longtext DEFAULT NULL,
  `fechacreacion` datetime(6) NOT NULL,
  `idCitaFk` int(11) NOT NULL,
  `idClienteFk` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `calificacion`
--

INSERT INTO `calificacion` (`idcalificacion`, `calificacion`, `comentario`, `fechacreacion`, `idCitaFk`, `idClienteFk`) VALUES
(1, 5, 'corte extupendo como nuestro presidente ABELARDO DE LA  ESPRIELLA', '2026-07-22 12:30:02.083867', 40, 11);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cita`
--

CREATE TABLE `cita` (
  `idCita` int(11) NOT NULL,
  `idBarberoFk` int(11) DEFAULT NULL,
  `idClienteFk` int(11) DEFAULT NULL,
  `idServicioFk` int(11) DEFAULT NULL,
  `idAgendaFk` int(11) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `horaInicio` time DEFAULT NULL,
  `observaciones` varchar(150) DEFAULT NULL,
  `idPagoFk` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cita`
--

INSERT INTO `cita` (`idCita`, `idBarberoFk`, `idClienteFk`, `idServicioFk`, `idAgendaFk`, `fecha`, `horaInicio`, `observaciones`, `idPagoFk`) VALUES
(1, 1, 1, 1, 1, '2026-03-20', '09:30:00', NULL, NULL),
(3, 1, 3, 5, 3, '2026-03-21', '10:15:00', NULL, NULL),
(4, 2, 4, 2, 4, '2026-03-21', '15:30:00', NULL, NULL),
(5, 1, 5, 4, 5, '2026-03-22', '09:00:00', NULL, NULL),
(6, 2, 6, 1, 6, '2026-03-22', '12:00:00', NULL, NULL),
(7, 1, 7, 6, 7, '2026-03-23', '11:30:00', NULL, NULL),
(9, 1, 9, 8, 9, '2026-03-24', '09:00:00', NULL, NULL),
(10, 2, 10, 9, 10, '2026-03-24', '10:00:00', NULL, NULL),
(18, 1, 1, 1, NULL, '2026-06-29', '10:00:00', NULL, NULL),
(19, 13, 1, 1, 1, '2026-06-28', '14:00:00', NULL, 1),
(20, 3, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(21, 5, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(22, 7, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(23, 9, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(24, 4, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(25, 6, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(26, 8, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(27, 10, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(28, 11, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(29, 12, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1),
(40, 11, 11, 1, 25, '2026-07-02', '08:00:00', 'Completado - Servicio realizado', 30),
(41, 11, 14, 2, 26, '2026-07-02', '09:00:00', 'Completado - Servicio realizado', 31),
(43, 11, 14, 18, 28, '2026-07-09', '08:00:00', 'uwu', 33);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cliente`
--

CREATE TABLE `cliente` (
  `idCliente` int(11) NOT NULL,
  `idUsuarioFk` int(11) DEFAULT NULL,
  `direccion` varchar(100) DEFAULT NULL,
  `fechaRegistro` date DEFAULT NULL,
  `contactoEmergencia` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cliente`
--

INSERT INTO `cliente` (`idCliente`, `idUsuarioFk`, `direccion`, `fechaRegistro`, `contactoEmergencia`) VALUES
(1, 4, 'Av. Amazonas', '2026-01-10', 'Maria-099'),
(3, 7, 'Condado', '2026-01-15', 'Ana-097'),
(4, 8, 'La Floresta', '2026-01-20', 'Luis-096'),
(5, 9, 'Quitumbe', '2026-01-25', 'Rosa-095'),
(6, 10, 'Cumbayá', '2026-01-28', 'Felipe-094'),
(7, 4, 'Av. Amazonas', '2026-02-01', 'Elena-093'),
(9, 7, 'Condado', '2026-02-10', 'Jose-098'),
(10, 8, 'La Floresta', '2026-02-15', 'Ana-097'),
(11, 16, 'Registrado desde la Web', '2026-06-18', 'No asignado'),
(14, 20, 'Registrado desde la Web', '2026-06-24', 'No asignado');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `configuracion_horario`
--

CREATE TABLE `configuracion_horario` (
  `id` bigint(20) NOT NULL,
  `hora_apertura` time(6) NOT NULL,
  `hora_cierre` time(6) NOT NULL,
  `intervalo_minutos` int(10) UNSIGNED NOT NULL CHECK (`intervalo_minutos` >= 0),
  `limite_citas_mensuales` int(10) UNSIGNED NOT NULL CHECK (`limite_citas_mensuales` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `configuracion_horario`
--

INSERT INTO `configuracion_horario` (`id`, `hora_apertura`, `hora_cierre`, `intervalo_minutos`, `limite_citas_mensuales`) VALUES
(1, '08:00:00.000000', '18:00:00.000000', 30, 3);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `dia_habilitado`
--

CREATE TABLE `dia_habilitado` (
  `id` bigint(20) NOT NULL,
  `fecha` date NOT NULL,
  `habilitado` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `dia_habilitado`
--

INSERT INTO `dia_habilitado` (`id`, `fecha`, `habilitado`) VALUES
(1, '2026-07-01', 1),
(2, '2026-07-02', 1),
(3, '2026-07-03', 1),
(4, '2026-07-04', 0),
(5, '2026-07-05', 0),
(6, '2026-07-06', 1),
(7, '2026-07-07', 1),
(8, '2026-07-08', 1),
(9, '2026-07-09', 1),
(10, '2026-07-10', 1),
(11, '2026-07-11', 0),
(12, '2026-07-12', 0),
(13, '2026-07-13', 1),
(14, '2026-07-14', 1),
(15, '2026-07-15', 1),
(16, '2026-07-16', 1),
(17, '2026-07-17', 1),
(18, '2026-07-18', 0),
(19, '2026-07-19', 0),
(20, '2026-07-20', 1),
(21, '2026-07-21', 1),
(22, '2026-07-22', 1),
(23, '2026-07-23', 1),
(24, '2026-07-24', 1),
(25, '2026-07-25', 0),
(26, '2026-07-26', 0),
(27, '2026-07-27', 1),
(28, '2026-07-28', 1),
(29, '2026-07-29', 1),
(30, '2026-07-30', 1),
(31, '2026-07-31', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(3, 'auth', 'group'),
(2, 'auth', 'permission'),
(4, 'auth', 'user'),
(5, 'contenttypes', 'contenttype'),
(9, 'negocio', 'agenda'),
(10, 'negocio', 'barbero'),
(17, 'negocio', 'barberodiahabilitado'),
(15, 'negocio', 'configuracionhorario'),
(16, 'negocio', 'diahabilitado'),
(14, 'reservas', 'cita'),
(23, 'servicios', 'agenda'),
(24, 'servicios', 'barbero'),
(11, 'servicios', 'cita'),
(25, 'servicios', 'cliente'),
(12, 'servicios', 'pago'),
(13, 'servicios', 'servicio'),
(26, 'servicios', 'usuario'),
(6, 'sessions', 'session'),
(27, 'usuarios', 'calificacion'),
(18, 'usuarios', 'cita'),
(19, 'usuarios', 'cliente'),
(22, 'usuarios', 'notificacion'),
(21, 'usuarios', 'perfilusuario'),
(7, 'usuarios', 'rol'),
(20, 'usuarios', 'servicio'),
(8, 'usuarios', 'usuario');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2026-06-11 01:43:29.337915'),
(2, 'auth', '0001_initial', '2026-06-11 01:43:29.924644'),
(3, 'admin', '0001_initial', '2026-06-11 01:43:30.068083'),
(4, 'admin', '0002_logentry_remove_auto_add', '2026-06-11 01:43:30.083633'),
(5, 'admin', '0003_logentry_add_action_flag_choices', '2026-06-11 01:43:30.104027'),
(6, 'contenttypes', '0002_remove_content_type_name', '2026-06-11 01:43:30.240275'),
(7, 'auth', '0002_alter_permission_name_max_length', '2026-06-11 01:43:30.334866'),
(8, 'auth', '0003_alter_user_email_max_length', '2026-06-11 01:43:30.357004'),
(9, 'auth', '0004_alter_user_username_opts', '2026-06-11 01:43:30.379493'),
(10, 'auth', '0005_alter_user_last_login_null', '2026-06-11 01:43:30.465411'),
(11, 'auth', '0006_require_contenttypes_0002', '2026-06-11 01:43:30.469350'),
(12, 'auth', '0007_alter_validators_add_error_messages', '2026-06-11 01:43:30.483737'),
(13, 'auth', '0008_alter_user_username_max_length', '2026-06-11 01:43:30.506462'),
(14, 'auth', '0009_alter_user_last_name_max_length', '2026-06-11 01:43:30.532763'),
(15, 'auth', '0010_alter_group_name_max_length', '2026-06-11 01:43:30.557398'),
(16, 'auth', '0011_update_proxy_permissions', '2026-06-11 01:43:30.576563'),
(17, 'auth', '0012_alter_user_first_name_max_length', '2026-06-11 01:43:30.600733'),
(18, 'sessions', '0001_initial', '2026-06-11 01:43:30.775234'),
(19, 'negocio', '0001_initial', '2026-06-11 01:44:07.691297'),
(20, 'servicios', '0001_initial', '2026-06-11 01:44:07.699780'),
(21, 'usuarios', '0001_initial', '2026-06-11 01:44:07.709572'),
(22, 'reservas', '0001_initial', '2026-06-17 06:01:38.666630'),
(23, 'negocio', '0002_configuracionhorario_diahabilitado', '2026-07-01 20:24:05.686588'),
(24, 'negocio', '0003_alter_configuracionhorario_id_alter_diahabilitado_id_and_more', '2026-07-01 20:59:29.749683'),
(25, 'usuarios', '0002_cita_cliente_servicio_perfilusuario_notificacion', '2026-07-02 00:38:56.875506'),
(26, 'servicios', '0002_agenda_barbero_cliente_usuario', '2026-07-02 00:52:25.138123'),
(27, 'usuarios', '0003_calificacion', '2026-07-17 19:38:38.253486');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('3i8hqj5a439xu8rb79kfnqrtmc7o1gzq', '.eJxVj00OgjAQhe_StSFQGUpZuvcMzdBppYqdpKUr490FQ4Juv_eT917CYFkmU7JLJpAYRCdOv2xE-3BxE-iO8caV5bikMFabpdrVXF2Z3HzZvX8FE-ZpTau6r7U_ezVqTZ6Ux0bVkjrbeSTXq14qDVYSqBZaqKXXAIBaNm1DYDWspdnlwNGEGGxAQjEsqbiTKLlgCmwiP8fktqEYgzh44vn7rDmQ54XFEMs8vz-zS1Z9:1wmXvY:VsS7Bovr4kQ63O-Zk7GJkVZEVSMHkAfrpnd-1xz4AVU', '2026-08-05 14:28:04.859625'),
('a9eerkejkf6mv4hsbiaw8v72wxnh7ogb', '.eJxVj00OwiAQha9iWJumBaYVly5NPAMZhtGiFRIoK-PdraaJun3f-8l7CIt1Hm0tnG3wYi9AbH81h3Tj-Ab-ivGSGkpxzsE1b0uz0tKckufpsHr_CkYs45I2sJM7JgDDg-r7VhGBdFrL86BbxUCkoO-0dhKMab3yzjN1zrQGOsPaLaWFS0jRhhgooEexn3PlrailYg7JxnR3mZepY8W4OWGsPIkvzmn6HJTPF0OTUVE:1wbgEu:EpN6BCPorYPAY8h2dmHtdwG6K60GQkvSLVQgssB5BLg', '2026-07-06 15:07:08.076477'),
('avgczg5y3i4uccct4edfx4nl1tkahju3', '.eJxVj00OgjAQhe_StSFQGUpZuvcMzdBppYqdpKUr490FQ4Juv_eT917CYFkmU7JLJpAYRCdOv2xE-3BxE-iO8caV5bikMFabpdrVXF2Z3HzZvX8FE-ZpTau6r7U_ezVqTZ6Ux0bVkjrbeSTXq14qDVYSqBZaqKXXAIBaNm1DYDWspdnlwNGEGGxAQjEsqbiTKLlgCmwiP8fktqEYgzh44vn7rDmQ54XFEMs8vz-zS1Z9:1wkjcF:Al9k-Y9_En4MSelWtg-nU6I69OtmZKAmhrEZ6ceu208', '2026-07-31 14:32:39.014945'),
('flnpiu40xr61wg4e83vj44di6knlm30b', '.eJxVjDEOwjAMRe-SGUVuUhqZkZ0zRI5jkwJKpaadKu4OlTrA-t97fzOR1qXEtckcx2wupjen3y0RP6XuID-o3ifLU13mMdldsQdt9jZleV0P9--gUCvfGkR7cuARgmNN4EPomFQdkiIGGCCx60RIBYgZs0MdGJn9GbMXNO8P9aE4xg:1waEJe:Ie39UtdKbDr0kz-AIjW1WKqTfo3skRVamJBIjMriw3s', '2026-07-02 15:06:02.592102'),
('fs60l91w68xadajzglyqlv4pe04469xt', '.eJxVj0tuhDAQRO_Sa4TAQ2PMcvZzBqtx28EJcUv-rKLcfcQIaZLte6VS1Q9YanW3rfhsI8MKM3R_2Ubuy6dT8CelD-mdpJrj1p-R_rKlfwj7435l_xXsVHZYQQ_LYMIt6M0YDqwDjXpQPLs5EPtFL0obdIpRTzjhoIJBRDJqnEZGZxA6KL5ESTam6CIxwVpz8x200ihHsUm-t-zPoZQivHmW4_VsfKMgVWBN7Th-n7NLVn0:1wewGw:CvaDz1aJKTprf-JR-t2Mri9MgzR-tQk2MeTDj6l93Vo', '2026-07-15 14:50:42.956166'),
('m37qj12g713d43akpcxqc7w88eyn2nfc', '.eJxVj8EOwiAQRP9lz01DsVtKj979BrJlwaIVEign47-bmibqdd7LZOYJhuq2mFpcNoFhggGa32wme3dxB3yjeE2tTXHLYW53pT1oaS-J3Xo-3L-ChcoCEygxCu1PXs1as2flqVNC8mAHT-xGNUql0UpG1WOPQnqNiKRl13eMViM0UFwJKZoQgw3EBNOWq2uglko5JBPTY85uH0oxwDfPaf08615vPTxO-Q:1wcP6q:8ftjTcLXAH0O328CfgWTbOaEmnp2-JGPNN2SPfBuSNs', '2026-07-08 15:01:48.007467'),
('nwdypz3bo5cldbh48xevs2wc2ybwpo8d', '.eJxVj8tuwyAQRX8lYp3YBAM2WWbfb0ADDDWpAxaPdlH132tXidpu7z3njuaTaGh11q1g1sGRCxnJ8W9mwL5h3At3g_iaOptizcF0O9I92tK9JIfL9cH-G5ihzJtNBUolheHeSD4wkDB4joJKK8aJgZ-4o6gmCcCZH5F5qpSRZ6BC2ZF52EYLlpCiDjHYAA7IpeaGR9JKgxySjuluMm6n7BIwVjw4PKwbYXb3CeW0_Lw5_EY-1bRZ_R1dgH7F7MOCpX_WjGp25oJxPp5urVUj5vn0zrsPNCv5-gbonWwJ:1weNXh:Ii3-hNesC2KJd1f4BbeVzMxNKB9djlTXuYBoiKTH1pE', '2026-07-14 01:45:41.287793'),
('tsztfxh77vy4yrhcwp30yhkeqmspwnjy', 'e30:1waCQ9:Tfze7UBPY1GidM51VXgFUEILPx8dq5tYKR_8sy7VGsc', '2026-07-02 13:04:37.781562');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `notificacion`
--

CREATE TABLE `notificacion` (
  `idnotificacion` int(11) NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `mensaje` varchar(255) NOT NULL,
  `leida` tinyint(1) NOT NULL,
  `fechacreacion` datetime(6) NOT NULL,
  `idUsuarioFk` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `notificacion`
--

INSERT INTO `notificacion` (`idnotificacion`, `tipo`, `mensaje`, `leida`, `fechacreacion`, `idUsuarioFk`) VALUES
(1, 'reserva_creada', 'Tu cita de Cambio de Imagen quedó reservada para el 03/07/2026 a las 10:30 con JUAN MANUEL RESTREPO.', 1, '2026-07-02 00:41:09.674877', 20),
(2, 'nueva_cita', 'CLIENTE UWU agendó el servicio de Cambio de Imagen para el 03/07/2026 a las 10:30.', 1, '2026-07-02 00:41:09.678897', 17),
(3, 'reserva_creada', 'Tu cita de Cambio de Imagen quedó reservada para el 09/07/2026 a las 08:00 con JUAN MANUEL RESTREPO.', 1, '2026-07-02 00:44:33.900077', 20),
(4, 'nueva_cita', 'CLIENTE UWU agendó el servicio de Cambio de Imagen para el 09/07/2026 a las 08:00.', 1, '2026-07-02 00:44:33.901494', 17),
(5, 'cita_confirmada', 'El barbero JUAN MANUEL RESTREPO confirmó exitosamente la cita de CLIENTE UWU (Perfilado Barba).', 0, '2026-07-02 01:08:36.272015', 1),
(6, 'cita_confirmada', 'El barbero JUAN MANUEL RESTREPO confirmó exitosamente la cita de CLIENTE UWU (Perfilado Barba).', 1, '2026-07-02 01:08:36.274949', 19);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pago`
--

CREATE TABLE `pago` (
  `idPago` int(11) NOT NULL,
  `metodoPago` varchar(35) DEFAULT NULL,
  `montoTotal` decimal(10,2) DEFAULT NULL,
  `fechaPago` datetime DEFAULT NULL,
  `estadoPago` enum('PAGADO','PENDIENTE','CANCELADO') DEFAULT NULL,
  `codigoFactura` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pago`
--

INSERT INTO `pago` (`idPago`, `metodoPago`, `montoTotal`, `fechaPago`, `estadoPago`, `codigoFactura`) VALUES
(1, 'Efectivo', 13.00, '2026-04-07 07:20:00', 'PAGADO', 'FAC-001'),
(2, 'Visa', 18.00, '2026-04-07 07:20:00', 'PAGADO', 'FAC-002'),
(3, 'Transferencia', 14.00, '2026-04-07 07:20:00', 'PENDIENTE', 'FAC-003'),
(4, 'Efectivo', 8.00, '2026-04-07 07:20:00', 'CANCELADO', 'FAC-004'),
(5, 'MasterCard', 15.00, '2026-04-07 07:20:00', 'PAGADO', 'FAC-005'),
(6, 'Efectivo', 13.00, '2026-04-07 07:20:00', 'PAGADO', 'FAC-006'),
(7, 'Transferencia', 25.00, '2026-04-07 07:20:00', 'PENDIENTE', 'FAC-007'),
(8, 'Visa', 10.00, '2026-04-07 07:20:00', 'PAGADO', 'FAC-008'),
(9, 'Efectivo', 5.00, '2026-04-07 07:20:00', 'PAGADO', 'FAC-009'),
(10, 'Visa', 14.00, '2026-04-07 07:20:00', 'PAGADO', 'FAC-010'),
(11, 'Efectivo', 18.00, '2026-06-18 14:33:22', 'PENDIENTE', 'FAC64796'),
(12, 'PSE', 20.00, '2026-06-18 14:40:54', 'PAGADO', 'FAC51120'),
(13, 'Efectivo', 20.00, '2026-06-18 14:47:54', 'PENDIENTE', 'FAC80466'),
(14, 'Efectivo', 26.00, '2026-06-18 15:33:06', 'PENDIENTE', 'FAC10719'),
(15, 'Efectivo', 28.00, '2026-06-18 15:35:41', 'PENDIENTE', 'FAC46469'),
(16, 'Efectivo', 32.00, '2026-06-23 23:05:22', 'PENDIENTE', 'FAC43980'),
(17, 'Efectivo', 10.00, '2026-06-23 23:06:10', 'PENDIENTE', 'FAC14939'),
(19, 'Efectivo', 60.00, '2026-06-23 23:15:03', 'PENDIENTE', 'FAC55873'),
(20, 'Efectivo', 13.00, '2026-07-01 19:02:25', 'PENDIENTE', 'FAC36055'),
(21, 'Efectivo', 13.00, '2026-07-01 20:33:48', 'PENDIENTE', 'FAC67079'),
(22, 'Efectivo', 13.00, '2026-07-01 20:33:48', 'PENDIENTE', 'FAC37212'),
(23, 'Efectivo', 13.00, '2026-07-01 20:43:34', 'PENDIENTE', 'FAC91749'),
(24, 'Efectivo', 13.00, '2026-07-01 20:45:14', 'PENDIENTE', 'FAC46992'),
(25, 'Efectivo', 13.00, '2026-07-01 20:47:33', 'PENDIENTE', 'FAC40226'),
(26, 'Efectivo', 13.00, '2026-07-01 20:47:33', 'PENDIENTE', 'FAC49482'),
(27, 'Efectivo', 13.00, '2026-07-01 21:43:43', 'PENDIENTE', 'FAC41236'),
(28, 'Efectivo', 28.00, '2026-07-01 21:52:40', 'PENDIENTE', 'FAC18986'),
(29, 'Efectivo', 35.00, '2026-07-01 21:53:05', 'PENDIENTE', 'FAC24588'),
(30, 'Efectivo', 13.00, '2026-07-01 23:57:38', 'PENDIENTE', 'FAC50955'),
(31, 'PSE', 8.00, '2026-07-01 23:58:53', 'PAGADO', 'FAC29513'),
(32, 'Efectivo', 35.00, '2026-07-02 00:41:09', 'PENDIENTE', 'FAC63556'),
(33, 'Efectivo', 35.00, '2026-07-02 00:44:33', 'PENDIENTE', 'FAC22379');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rol`
--

CREATE TABLE `rol` (
  `idRol` int(11) NOT NULL,
  `nombreRol` varchar(15) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `rol`
--

INSERT INTO `rol` (`idRol`, `nombreRol`) VALUES
(1, 'Admin'),
(2, 'Barbero'),
(3, 'Cliente');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `servicio`
--

CREATE TABLE `servicio` (
  `idServicio` int(11) NOT NULL,
  `nombreServicio` varchar(60) DEFAULT NULL,
  `duracion` int(11) DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT NULL,
  `tipoServicio` varchar(50) DEFAULT NULL,
  `imagen` varchar(255) DEFAULT 'default.jpg'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `servicio`
--

INSERT INTO `servicio` (`idServicio`, `nombreServicio`, `duracion`, `precio`, `tipoServicio`, `imagen`) VALUES
(1, 'Corte Tradicional', 35, 13.00, 'Individual', 'servicios/corte-tradicional.webp'),
(2, 'Perfilado Barba', 25, 8.00, 'Individual', 'servicios/perfilado-barba.jpeg'),
(3, 'Combo', 60, 18.00, 'Paquete', 'servicios/paquete2_Ze45uN7.jpg'),
(4, 'Facial', 30, 15.00, 'Paquete', 'servicios/servicios-limpieza1_kA5HtA0.jpg'),
(5, 'Fade', 45, 14.00, 'Individual', 'servicios/fade.jpg'),
(6, 'Tinte', 60, 25.00, 'Paquete', 'servicios/tinte-cabello.jpg'),
(7, 'Líneas', 15, 5.00, 'Paquete', 'servicios/diseño-lineas.jpeg'),
(8, 'Lavado cabello', 10, 5.00, 'Individual', 'servicios/servicios-lavado.avif'),
(9, 'Cejas', 15, 4.00, 'Individual', 'servicios/cejas.jpg'),
(10, 'Mascarilla', 20, 10.00, 'Individual', 'servicios/servicios-mascarilla.jpg'),
(11, 'Corte Clásico + Cejas', 45, 20.00, 'Paquete', 'servicios/cejas_hWSiah3.jpg'),
(12, 'Perfil Perfecto', 50, 22.00, 'Paquete', 'servicios/paquete2.jpg'),
(14, 'Corte personalizado', 60, 26.00, 'Paquete', 'servicios/paquete5.jpg'),
(15, 'Look Completo', 70, 28.00, 'Paquete', 'servicios/paquete5.jpg'),
(16, 'Combo de limpieza facial', 80, 30.00, 'Paquete', 'servicios/paquete6.jpg'),
(17, 'Imagen Ejecutiva', 90, 32.00, 'Paquete', 'servicios/paquete4.jpeg'),
(18, 'Cambio de Imagen', 90, 35.00, 'Paquete', 'servicios/paquete3.jpg'),
(19, 'Experiencia Premium', 140, 60.00, 'Paquete', 'servicios/masaje-capilar.jpeg');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `idUsuario` int(11) NOT NULL,
  `cedula` varchar(15) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `correoUsuario` varchar(50) DEFAULT NULL,
  `numCelular` varchar(15) DEFAULT NULL,
  `contrasena` varchar(200) DEFAULT NULL,
  `fechaNacimiento` date DEFAULT NULL,
  `idRolFk` int(11) DEFAULT NULL,
  `foto_perfil` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`idUsuario`, `cedula`, `nombre`, `correoUsuario`, `numCelular`, `contrasena`, `fechaNacimiento`, `idRolFk`, `foto_perfil`) VALUES
(1, '1723456789', 'ANDRÉS MENDOZA', 'a.mendoza@mya.com', '0998765432', NULL, NULL, 1, NULL),
(2, '1755842100', 'MATEO ALVEAR', 'mateo.barber@mya.com', '0984455667', NULL, NULL, 2, ''),
(3, '1004556772', 'LUIS SIMBAÑA', 'luis.barber@mya.com', '0977889900', NULL, NULL, 2, ''),
(4, '0503441288', 'CARLOS PÉREZ', 'carlitos@gmail.com', '0912233445', NULL, NULL, 3, ''),
(5, '1711223344', 'JUAN RODRÍGUEZ', 'juan.rod@outlook.com', '0955667788', NULL, NULL, 3, ''),
(7, '0988776655', 'DIEGO FERNÁNDEZ', 'diego.fer@gmail.com', '0922446688', NULL, NULL, 3, ''),
(8, '1788990011', 'ROBERTO GÓMEZ', 'roberto@gmail.com', '0933557799', NULL, NULL, 3, ''),
(9, '1744556611', 'LUCÍA TORRES', 'lucia@gmail.com', '0944668800', NULL, NULL, 3, ''),
(10, '1722334455', 'PEDRO SALAS', 'pedro@gmail.com', '0955779911', NULL, NULL, 3, ''),
(13, '1111111111', 'SAMUEL LINARES', 'samueluwu@gmail.com', '3333333333', 'samuel', '2026-06-24', 3, ''),
(14, '2222222', 'JIMENA  HERNÁNDEZ', 'jimena@gmail.com', '3239343409', 'jimena123', '2008-03-24', 3, ''),
(16, '1122334455', 'JAMES ABELARDO DIAZ URIBE', 'derecha@gmail.com', '3216579435', 'pbkdf2_sha256$600000$mm9X4dXuc8FX83wY4CvHAu$S3tiZPZarh+2ysTwOTmcLIW8ibjLCUfdKjQ9LMU0Owg=', '1988-04-20', 3, ''),
(17, '35919743', 'JUAN MANUEL RESTREPO', 'restrepo123@gmail.com', '3427685463', 'pbkdf2_sha256$600000$Ui57A5R99oF2FSYuJdWQWu$S3PjXGv17+nJfSOMUXEDj8z/TdGK8/4B6gqwgKLTQA0=', '1989-08-12', 2, 'perfiles/usuario_17_descarga.webp'),
(19, '4444444444', 'DANI JORDIWILDE', 'dani@gmail.com', '22222222222', 'pbkdf2_sha256$600000$ud3U9yK19LvNUYSFpWdxuA$wSPZm1V3A8E2of2uJ9oX39DgBkfzwf3u/vM/rHVvTh0=', '2026-06-16', 1, NULL),
(20, '1111222333', 'CLIENTE UWU', 'cliente@gmail.com', '3334445555', 'pbkdf2_sha256$600000$A8DpsiokPP0k1bHK7pPT96$v8G4lzCykQndKOJ2OJKPRj2YtCb3dCyOKAZmLlVPaHI=', '2026-06-25', 3, 'perfiles/usuario_20_21452447-juutb5hh-v4.webp'),
(21, '1111111112', 'NUEVO BARBERO', 'barbero.nuevo@mya.com', '0999999999', NULL, NULL, 2, '');

--
-- Disparadores `usuario`
--
DELIMITER $$
CREATE TRIGGER `FormatearNombreUsuario` BEFORE INSERT ON `usuario` FOR EACH ROW BEGIN
    SET NEW.nombre = UPPER(NEW.nombre);
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios_perfilusuario`
--

CREATE TABLE `usuarios_perfilusuario` (
  `id` bigint(20) NOT NULL,
  `rol` varchar(20) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vistapagosexitosos`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vistapagosexitosos` (
`codigoFactura` varchar(20)
,`metodoPago` varchar(35)
,`montoTotal` decimal(10,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vistaproximasagendas`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vistaproximasagendas` (
`fecha` date
,`horaInicio` time
,`barbero` varchar(100)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vistarankingservicios`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `vistarankingservicios` (
`nombreServicio` varchar(60)
,`vecesSolicitado` bigint(21)
);

-- --------------------------------------------------------

--
-- Estructura para la vista `vistapagosexitosos`
--
DROP TABLE IF EXISTS `vistapagosexitosos`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vistapagosexitosos`  AS SELECT `pago`.`codigoFactura` AS `codigoFactura`, `pago`.`metodoPago` AS `metodoPago`, `pago`.`montoTotal` AS `montoTotal` FROM `pago` WHERE `pago`.`estadoPago` = 'PAGADO' ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vistaproximasagendas`
--
DROP TABLE IF EXISTS `vistaproximasagendas`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vistaproximasagendas`  AS SELECT `a`.`fecha` AS `fecha`, `a`.`horaInicio` AS `horaInicio`, `u`.`nombre` AS `barbero` FROM ((`agenda` `a` join `barbero` `b` on(`a`.`idBarberoFk` = `b`.`idBarbero`)) join `usuario` `u` on(`b`.`idUsuarioFk` = `u`.`idUsuario`)) WHERE `a`.`fecha` >= curdate() ;

-- --------------------------------------------------------

--
-- Estructura para la vista `vistarankingservicios`
--
DROP TABLE IF EXISTS `vistarankingservicios`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vistarankingservicios`  AS SELECT `s`.`nombreServicio` AS `nombreServicio`, count(`c`.`idCita`) AS `vecesSolicitado` FROM (`servicio` `s` left join `cita` `c` on(`s`.`idServicio` = `c`.`idServicioFk`)) GROUP BY `s`.`nombreServicio` ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `agenda`
--
ALTER TABLE `agenda`
  ADD PRIMARY KEY (`idAgenda`),
  ADD KEY `fk_agenda_barbero` (`idBarberoFk`);

--
-- Indices de la tabla `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indices de la tabla `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Indices de la tabla `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Indices de la tabla `auth_user`
--
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indices de la tabla `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);

--
-- Indices de la tabla `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  ADD KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`);

--
-- Indices de la tabla `barbero`
--
ALTER TABLE `barbero`
  ADD PRIMARY KEY (`idBarbero`),
  ADD KEY `fk_barbero_usuario` (`idUsuarioFk`);

--
-- Indices de la tabla `barbero_dia_habilitado`
--
ALTER TABLE `barbero_dia_habilitado`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `barbero_dia_habilitado_idusuariofk_fecha_12b490a9_uniq` (`idusuariofk`,`fecha`);

--
-- Indices de la tabla `calificacion`
--
ALTER TABLE `calificacion`
  ADD PRIMARY KEY (`idcalificacion`),
  ADD UNIQUE KEY `idCitaFk` (`idCitaFk`),
  ADD KEY `calificacion_idClienteFk_95e3eed3_fk_cliente_idCliente` (`idClienteFk`);

--
-- Indices de la tabla `cita`
--
ALTER TABLE `cita`
  ADD PRIMARY KEY (`idCita`),
  ADD KEY `idx_fecha_cita` (`fecha`),
  ADD KEY `fk_cita_barbero` (`idBarberoFk`),
  ADD KEY `fk_cita_cliente` (`idClienteFk`),
  ADD KEY `fk_cita_servicio` (`idServicioFk`),
  ADD KEY `fk_cita_agenda` (`idAgendaFk`),
  ADD KEY `fk_cita_pago` (`idPagoFk`);

--
-- Indices de la tabla `cliente`
--
ALTER TABLE `cliente`
  ADD PRIMARY KEY (`idCliente`),
  ADD KEY `fk_cliente_usuario` (`idUsuarioFk`);

--
-- Indices de la tabla `configuracion_horario`
--
ALTER TABLE `configuracion_horario`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `dia_habilitado`
--
ALTER TABLE `dia_habilitado`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `fecha` (`fecha`);

--
-- Indices de la tabla `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`);

--
-- Indices de la tabla `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Indices de la tabla `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- Indices de la tabla `notificacion`
--
ALTER TABLE `notificacion`
  ADD PRIMARY KEY (`idnotificacion`),
  ADD KEY `notificacion_idUsuarioFk_b84fac34_fk_usuario_idUsuario` (`idUsuarioFk`);

--
-- Indices de la tabla `pago`
--
ALTER TABLE `pago`
  ADD PRIMARY KEY (`idPago`);

--
-- Indices de la tabla `rol`
--
ALTER TABLE `rol`
  ADD PRIMARY KEY (`idRol`);

--
-- Indices de la tabla `servicio`
--
ALTER TABLE `servicio`
  ADD PRIMARY KEY (`idServicio`);

--
-- Indices de la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`idUsuario`),
  ADD UNIQUE KEY `cedula` (`cedula`),
  ADD KEY `idx_correo_usuario` (`correoUsuario`),
  ADD KEY `fk_usuario_rol` (`idRolFk`);

--
-- Indices de la tabla `usuarios_perfilusuario`
--
ALTER TABLE `usuarios_perfilusuario`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `agenda`
--
ALTER TABLE `agenda`
  MODIFY `idAgenda` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT de la tabla `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=109;

--
-- AUTO_INCREMENT de la tabla `auth_user`
--
ALTER TABLE `auth_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `barbero`
--
ALTER TABLE `barbero`
  MODIFY `idBarbero` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT de la tabla `barbero_dia_habilitado`
--
ALTER TABLE `barbero_dia_habilitado`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `calificacion`
--
ALTER TABLE `calificacion`
  MODIFY `idcalificacion` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `cita`
--
ALTER TABLE `cita`
  MODIFY `idCita` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=44;

--
-- AUTO_INCREMENT de la tabla `cliente`
--
ALTER TABLE `cliente`
  MODIFY `idCliente` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT de la tabla `configuracion_horario`
--
ALTER TABLE `configuracion_horario`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `dia_habilitado`
--
ALTER TABLE `dia_habilitado`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT de la tabla `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT de la tabla `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT de la tabla `notificacion`
--
ALTER TABLE `notificacion`
  MODIFY `idnotificacion` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `pago`
--
ALTER TABLE `pago`
  MODIFY `idPago` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=34;

--
-- AUTO_INCREMENT de la tabla `rol`
--
ALTER TABLE `rol`
  MODIFY `idRol` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `servicio`
--
ALTER TABLE `servicio`
  MODIFY `idServicio` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=35;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `idUsuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT de la tabla `usuarios_perfilusuario`
--
ALTER TABLE `usuarios_perfilusuario`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `agenda`
--
ALTER TABLE `agenda`
  ADD CONSTRAINT `fk_agenda_barbero` FOREIGN KEY (`idBarberoFk`) REFERENCES `barbero` (`idBarbero`);

--
-- Filtros para la tabla `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Filtros para la tabla `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Filtros para la tabla `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Filtros para la tabla `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Filtros para la tabla `barbero`
--
ALTER TABLE `barbero`
  ADD CONSTRAINT `fk_barbero_usuario` FOREIGN KEY (`idUsuarioFk`) REFERENCES `usuario` (`idUsuario`) ON DELETE CASCADE;

--
-- Filtros para la tabla `calificacion`
--
ALTER TABLE `calificacion`
  ADD CONSTRAINT `calificacion_idCitaFk_13262db1_fk_cita_idCita` FOREIGN KEY (`idCitaFk`) REFERENCES `cita` (`idCita`),
  ADD CONSTRAINT `calificacion_idClienteFk_95e3eed3_fk_cliente_idCliente` FOREIGN KEY (`idClienteFk`) REFERENCES `cliente` (`idCliente`);

--
-- Filtros para la tabla `cita`
--
ALTER TABLE `cita`
  ADD CONSTRAINT `fk_cita_agenda` FOREIGN KEY (`idAgendaFk`) REFERENCES `agenda` (`idAgenda`),
  ADD CONSTRAINT `fk_cita_barbero` FOREIGN KEY (`idBarberoFk`) REFERENCES `barbero` (`idBarbero`),
  ADD CONSTRAINT `fk_cita_cliente` FOREIGN KEY (`idClienteFk`) REFERENCES `cliente` (`idCliente`),
  ADD CONSTRAINT `fk_cita_pago` FOREIGN KEY (`idPagoFk`) REFERENCES `pago` (`idPago`),
  ADD CONSTRAINT `fk_cita_servicio` FOREIGN KEY (`idServicioFk`) REFERENCES `servicio` (`idServicio`);

--
-- Filtros para la tabla `cliente`
--
ALTER TABLE `cliente`
  ADD CONSTRAINT `fk_cliente_usuario` FOREIGN KEY (`idUsuarioFk`) REFERENCES `usuario` (`idUsuario`) ON DELETE CASCADE;

--
-- Filtros para la tabla `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Filtros para la tabla `notificacion`
--
ALTER TABLE `notificacion`
  ADD CONSTRAINT `notificacion_idUsuarioFk_b84fac34_fk_usuario_idUsuario` FOREIGN KEY (`idUsuarioFk`) REFERENCES `usuario` (`idUsuario`);

--
-- Filtros para la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `fk_usuario_rol` FOREIGN KEY (`idRolFk`) REFERENCES `rol` (`idRol`);

--
-- Filtros para la tabla `usuarios_perfilusuario`
--
ALTER TABLE `usuarios_perfilusuario`
  ADD CONSTRAINT `usuarios_perfilusuario_user_id_f03197c5_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
