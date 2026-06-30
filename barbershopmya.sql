-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 30-06-2026 a las 03:46:07
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

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
(2, 2, '2026-03-20', '10:00:00', '14:00:00'),
(3, 1, '2026-03-21', '09:00:00', '13:00:00'),
(4, 2, '2026-03-21', '15:00:00', '19:00:00'),
(5, 1, '2026-03-22', '09:00:00', '13:00:00'),
(6, 2, '2026-03-22', '10:00:00', '14:00:00'),
(7, 1, '2026-03-23', '09:00:00', '13:00:00'),
(8, 2, '2026-03-23', '10:00:00', '14:00:00'),
(9, 1, '2026-03-24', '09:00:00', '13:00:00'),
(10, 2, '2026-03-24', '10:00:00', '14:00:00'),
(11, 11, '2026-06-24', '08:00:00', NULL),
(12, 11, '2026-06-25', '09:00:00', NULL),
(14, 11, '2026-06-30', '08:00:00', NULL);

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
(56, 'Can view cita', 14, 'view_cita');

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
(4, 'pbkdf2_sha256$600000$HQyAPOsaeV4ROmnxySJedH$ZIhfWy/uWH5wQuBlx0fMsj8PE3yqJ+NTwF+IFlyhNLI=', '2026-06-18 15:06:02.585858', 0, 'derecha@gmail.com', 'James Abelardo', 'Diaz Uribe', 'derecha@gmail.com', 0, 1, '2026-06-18 15:05:47.242567'),
(5, 'pbkdf2_sha256$600000$m6HPb4HxtCJuGyFL53Zkio$ZKD43nyF1vSI5De/JhT+prnMur1yLWocqvDYXQ3lDDU=', '2026-06-30 01:32:21.733661', 0, 'restrepo123@gmail.com', 'Juan Manuel', 'Restrepo', 'restrepo123@gmail.com', 0, 1, '2026-06-22 14:05:23.921634'),
(6, 'pbkdf2_sha256$600000$82sfzCGHimPQKppeCsm30C$eWVhhE4604zJXJhoX0I55EplXFtsEdR8EEh9ZsMVUYI=', '2026-06-30 01:27:36.650317', 0, 'dani@gmail.com', 'dani', 'jordiwilde', 'dani@gmail.com', 0, 1, '2026-06-23 21:06:43.304259'),
(7, 'pbkdf2_sha256$600000$bHYobMHyjKR6Z942ya8elC$xF5a5TWtJQbJzNjXJJU6ahMARJC9sSavvzeU4vs6Ess=', '2026-06-30 01:45:41.282185', 0, 'cliente@gmail.com', 'cliente de prueba', 'uwu', 'cliente@gmail.com', 0, 1, '2026-06-24 20:17:49.165423');

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
(13, 21, 'Cortes Clásicos');

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
(2, 2, 2, 3, 2, '2026-03-20', '11:00:00', NULL, NULL),
(3, 1, 3, 5, 3, '2026-03-21', '10:15:00', NULL, NULL),
(4, 2, 4, 2, 4, '2026-03-21', '15:30:00', NULL, NULL),
(5, 1, 5, 4, 5, '2026-03-22', '09:00:00', NULL, NULL),
(6, 2, 6, 1, 6, '2026-03-22', '12:00:00', NULL, NULL),
(7, 1, 7, 6, 7, '2026-03-23', '11:30:00', NULL, NULL),
(8, 2, 8, 7, 8, '2026-03-23', '12:00:00', NULL, NULL),
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
(29, 12, 1, 1, 1, '2026-06-28', '09:00:00', NULL, 1);

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
(2, 6, 'Calle Larga', '2026-01-12', 'Jose-098'),
(3, 7, 'Condado', '2026-01-15', 'Ana-097'),
(4, 8, 'La Floresta', '2026-01-20', 'Luis-096'),
(5, 9, 'Quitumbe', '2026-01-25', 'Rosa-095'),
(6, 10, 'Cumbayá', '2026-01-28', 'Felipe-094'),
(7, 4, 'Av. Amazonas', '2026-02-01', 'Elena-093'),
(8, 6, 'Calle Larga', '2026-02-05', 'Maria-099'),
(9, 7, 'Condado', '2026-02-10', 'Jose-098'),
(10, 8, 'La Floresta', '2026-02-15', 'Ana-097'),
(11, 16, 'Registrado desde la Web', '2026-06-18', 'No asignado'),
(14, 20, 'Registrado desde la Web', '2026-06-24', 'No asignado');

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
(14, 'reservas', 'cita'),
(11, 'servicios', 'cita'),
(12, 'servicios', 'pago'),
(13, 'servicios', 'servicio'),
(6, 'sessions', 'session'),
(7, 'usuarios', 'rol'),
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
(22, 'reservas', '0001_initial', '2026-06-17 06:01:38.666630');

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
('a9eerkejkf6mv4hsbiaw8v72wxnh7ogb', '.eJxVj00OwiAQha9iWJumBaYVly5NPAMZhtGiFRIoK-PdraaJun3f-8l7CIt1Hm0tnG3wYi9AbH81h3Tj-Ab-ivGSGkpxzsE1b0uz0tKckufpsHr_CkYs45I2sJM7JgDDg-r7VhGBdFrL86BbxUCkoO-0dhKMab3yzjN1zrQGOsPaLaWFS0jRhhgooEexn3PlrailYg7JxnR3mZepY8W4OWGsPIkvzmn6HJTPF0OTUVE:1wbgEu:EpN6BCPorYPAY8h2dmHtdwG6K60GQkvSLVQgssB5BLg', '2026-07-06 15:07:08.076477'),
('flnpiu40xr61wg4e83vj44di6knlm30b', '.eJxVjDEOwjAMRe-SGUVuUhqZkZ0zRI5jkwJKpaadKu4OlTrA-t97fzOR1qXEtckcx2wupjen3y0RP6XuID-o3ifLU13mMdldsQdt9jZleV0P9--gUCvfGkR7cuARgmNN4EPomFQdkiIGGCCx60RIBYgZs0MdGJn9GbMXNO8P9aE4xg:1waEJe:Ie39UtdKbDr0kz-AIjW1WKqTfo3skRVamJBIjMriw3s', '2026-07-02 15:06:02.592102'),
('m37qj12g713d43akpcxqc7w88eyn2nfc', '.eJxVj8EOwiAQRP9lz01DsVtKj979BrJlwaIVEign47-bmibqdd7LZOYJhuq2mFpcNoFhggGa32wme3dxB3yjeE2tTXHLYW53pT1oaS-J3Xo-3L-ChcoCEygxCu1PXs1as2flqVNC8mAHT-xGNUql0UpG1WOPQnqNiKRl13eMViM0UFwJKZoQgw3EBNOWq2uglko5JBPTY85uH0oxwDfPaf08615vPTxO-Q:1wcP6q:8ftjTcLXAH0O328CfgWTbOaEmnp2-JGPNN2SPfBuSNs', '2026-07-08 15:01:48.007467'),
('nwdypz3bo5cldbh48xevs2wc2ybwpo8d', '.eJxVj8tuwyAQRX8lYp3YBAM2WWbfb0ADDDWpAxaPdlH132tXidpu7z3njuaTaGh11q1g1sGRCxnJ8W9mwL5h3At3g_iaOptizcF0O9I92tK9JIfL9cH-G5ihzJtNBUolheHeSD4wkDB4joJKK8aJgZ-4o6gmCcCZH5F5qpSRZ6BC2ZF52EYLlpCiDjHYAA7IpeaGR9JKgxySjuluMm6n7BIwVjw4PKwbYXb3CeW0_Lw5_EY-1bRZ_R1dgH7F7MOCpX_WjGp25oJxPp5urVUj5vn0zrsPNCv5-gbonWwJ:1weNXh:Ii3-hNesC2KJd1f4BbeVzMxNKB9djlTXuYBoiKTH1pE', '2026-07-14 01:45:41.287793'),
('tsztfxh77vy4yrhcwp30yhkeqmspwnjy', 'e30:1waCQ9:Tfze7UBPY1GidM51VXgFUEILPx8dq5tYKR_8sy7VGsc', '2026-07-02 13:04:37.781562');

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
(19, 'Efectivo', 60.00, '2026-06-23 23:15:03', 'PENDIENTE', 'FAC55873');

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
(3, 'Combo', 60, 18.00, 'Paquete', 'servicios/paquete1.jpg'),
(4, 'Facial', 30, 15.00, 'Paquete', 'servicios/servicios-limpieza1.jpg'),
(5, 'Fade', 45, 14.00, 'Individual', 'servicios/fade.jpg'),
(6, 'Tinte', 60, 25.00, 'Paquete', 'servicios/tinte-cabello.jpg'),
(7, 'Líneas', 15, 5.00, 'Paquete', 'servicios/diseño-lineas.jpeg'),
(8, 'Lavado', 10, 5.00, 'Individual', 'servicios/servicios-lavado.avif'),
(9, 'Cejas', 15, 4.00, 'Individual', 'servicios/servicios-cejas.png'),
(10, 'Mascarilla', 20, 10.00, 'Individual', 'servicios/servicios-mascarilla.jpg'),
(11, 'Corte Clásico + Cejas', 45, 20.00, 'Paquete', 'servicios/paquete1.jpg'),
(12, 'Perfil Perfecto', 50, 22.00, 'Paquete', 'servicios/paquete2.jpg'),
(13, 'Barba + Cejas', 40, 18.00, 'Paquete', 'servicios/paquete3.jpg'),
(14, 'Corte personalizado', 60, 26.00, 'Paquete', 'servicios/paquete4.jpeg'),
(15, 'Look Completo', 70, 28.00, 'Paquete', 'servicios/paquete5.jpg'),
(16, 'Combo de limpieza facial', 80, 30.00, 'Paquete', 'servicios/paquete6.jpg'),
(17, 'Imagen Ejecutiva', 90, 32.00, 'Paquete', 'servicios/paquete7.jpeg'),
(18, 'Cambio de Imagen', 90, 35.00, 'Paquete', 'servicios/paquete8.jpg'),
(19, 'Experiencia Premium', 140, 60.00, 'Paquete', 'servicios/paquete9.jpeg'),
(21, 'Cejassss', 15, 500.00, 'Individual', 'servicios/logo.jpeg');

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
(2, '1755842100', 'MATEO ALVEAR', 'mateo.barber@mya.com', '0984455667', NULL, NULL, 2, NULL),
(3, '1004556772', 'LUIS SIMBAÑA', 'luis.barber@mya.com', '0977889900', NULL, NULL, 2, NULL),
(4, '0503441288', 'CARLOS PÉREZ', 'carlitos@gmail.com', '0912233445', NULL, NULL, 3, NULL),
(5, '1711223344', 'JUAN RODRÍGUEZ', 'juan.rod@outlook.com', '0955667788', NULL, NULL, 3, NULL),
(6, '1204885991', 'ANA GARCÍA', 'ana.garcia@hotmail.com', '0966112233', NULL, NULL, 3, NULL),
(7, '0988776655', 'DIEGO FERNÁNDEZ', 'diego.fer@gmail.com', '0922446688', NULL, NULL, 3, ''),
(8, '1788990011', 'ROBERTO GÓMEZ', 'roberto@gmail.com', '0933557799', NULL, NULL, 3, NULL),
(9, '1744556611', 'LUCÍA TORRES', 'lucia@gmail.com', '0944668800', NULL, NULL, 3, NULL),
(10, '1722334455', 'PEDRO SALAS', 'pedro@gmail.com', '0955779911', NULL, NULL, 3, NULL),
(13, '1111111111', 'SAMUEL LINARES', 'samueluwu@gmail.com', '3333333333', 'samuel', '2026-06-24', 3, NULL),
(14, '2222222', 'JIMENA  HERNÁNDEZ', 'jimena@gmail.com', '3239343409', 'jimena123', '2008-03-24', 3, NULL),
(16, '1122334455', 'JAMES ABELARDO DIAZ URIBE', 'derecha@gmail.com', '3216579435', 'pbkdf2_sha256$600000$mm9X4dXuc8FX83wY4CvHAu$S3tiZPZarh+2ysTwOTmcLIW8ibjLCUfdKjQ9LMU0Owg=', '1988-04-20', 3, NULL),
(17, '35919743', 'JUAN MANUEL RESTREPO', 'restrepo123@gmail.com', '3427685463', 'pbkdf2_sha256$600000$Ui57A5R99oF2FSYuJdWQWu$S3PjXGv17+nJfSOMUXEDj8z/TdGK8/4B6gqwgKLTQA0=', '1989-08-12', 2, 'perfiles/usuario_17_descarga.webp'),
(19, '4444444444', 'DANI JORDIWILDE', 'dani@gmail.com', '22222222222', 'pbkdf2_sha256$600000$ud3U9yK19LvNUYSFpWdxuA$wSPZm1V3A8E2of2uJ9oX39DgBkfzwf3u/vM/rHVvTh0=', '2026-06-16', 1, NULL),
(20, '1111222333', 'CLIENTE UWU', 'cliente@gmail.com', '3334445555', 'pbkdf2_sha256$600000$A8DpsiokPP0k1bHK7pPT96$v8G4lzCykQndKOJ2OJKPRj2YtCb3dCyOKAZmLlVPaHI=', '2026-06-25', 3, 'perfiles/usuario_20_21452447-juutb5hh-v4.webp'),
(21, '1111111112', 'NUEVO BARBERO', 'barbero.nuevo@mya.com', '0999999999', NULL, NULL, 2, NULL);

--
-- Disparadores `usuario`
--
DELIMITER $$
CREATE TRIGGER `AntesEliminarUsuario` BEFORE DELETE ON `usuario` FOR EACH ROW BEGIN
    IF OLD.idRolFk = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede eliminar al Administrador principal';
    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `DespuesActualizarUsuarioCambioRol` AFTER UPDATE ON `usuario` FOR EACH ROW BEGIN
    -- VALIDAR SI REALMENTE CAMBIÓ EL ROL
    IF OLD.idRolFk != NEW.idRolFk THEN
        
        -- ================================================
        -- CASO A: EL NUEVO ROL ES BARBERO (Rol 2)
        -- ================================================
        IF NEW.idRolFk = 2 THEN
            -- 1. Borrar de la tabla del rol anterior (Cliente)
            DELETE FROM cliente WHERE idUsuarioFk = NEW.idUsuario;
            
            -- 2. Insertar en la nueva tabla (Barbero) si no existe ya
            IF NOT EXISTS (SELECT 1 FROM barbero WHERE idUsuarioFk = NEW.idUsuario) THEN
                INSERT INTO barbero (idUsuarioFk, especialidad) 
                VALUES (NEW.idUsuario, 'Por asignar');
            END IF;

        -- ================================================
        -- CASO B: EL NUEVO ROL ES CLIENTE (Rol 3)
        -- ================================================
        ELSEIF NEW.idRolFk = 3 THEN
            -- 1. Borrar de la tabla del rol anterior (Barbero)
            DELETE FROM barbero WHERE idUsuarioFk = NEW.idUsuario;
            
            -- 2. Insertar en la nueva tabla (Cliente) si no existe ya
            IF NOT EXISTS (SELECT 1 FROM cliente WHERE idUsuarioFk = NEW.idUsuario) THEN
                INSERT INTO cliente (idUsuarioFk, direccion, fechaRegistro, contactoEmergencia) 
                VALUES (NEW.idUsuario, 'Cambio de Rol desde Panel', CURDATE(), 'No asignado');
            END IF;

        -- ================================================
        -- CASO C: PASÓ A SER ADMIN (Rol 1) u OTRO
        -- ================================================
        ELSE
            -- Si pasa a ser Admin, lo removemos de ambas tablas operativas
            DELETE FROM barbero WHERE idUsuarioFk = NEW.idUsuario;
            DELETE FROM cliente WHERE idUsuarioFk = NEW.idUsuario;
        END IF;
        
    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `DespuesInsertarUsuarioClasificarRol` AFTER INSERT ON `usuario` FOR EACH ROW BEGIN
    -- Si es Barbero (Rol 2)
    IF NEW.idRolFk = 2 THEN
        INSERT INTO barbero (idUsuarioFk, especialidad) 
        VALUES (NEW.idUsuario, 'Por asignar');
        
    -- Si es Cliente (Rol 3)
    ELSEIF NEW.idRolFk = 3 THEN
        INSERT INTO cliente (idUsuarioFk, direccion, fechaRegistro, contactoEmergencia) 
        VALUES (NEW.idUsuario, 'Registrado desde la Web', CURDATE(), 'No asignado');
    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `FormatearNombreUsuario` BEFORE INSERT ON `usuario` FOR EACH ROW BEGIN
    SET NEW.nombre = UPPER(NEW.nombre);
END
$$
DELIMITER ;

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
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `agenda`
--
ALTER TABLE `agenda`
  MODIFY `idAgenda` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

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
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=57;

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
  MODIFY `idBarbero` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT de la tabla `cita`
--
ALTER TABLE `cita`
  MODIFY `idCita` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30;

--
-- AUTO_INCREMENT de la tabla `cliente`
--
ALTER TABLE `cliente`
  MODIFY `idCliente` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT de la tabla `pago`
--
ALTER TABLE `pago`
  MODIFY `idPago` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT de la tabla `rol`
--
ALTER TABLE `rol`
  MODIFY `idRol` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `servicio`
--
ALTER TABLE `servicio`
  MODIFY `idServicio` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=34;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `idUsuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

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
-- Filtros para la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `fk_usuario_rol` FOREIGN KEY (`idRolFk`) REFERENCES `rol` (`idRol`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
