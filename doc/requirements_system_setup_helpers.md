# Requirements Specification — System Setup Helpers

## Document Info

| Field | Value |
|---|---|
| Software | System Setup Helpers |
| Version | 1.0 |
| Status | Approved |

---

## 1. Overview

System setup helpers is a collection of tools to assist an experienced developer in setting up the system, including cloning repositories, configuring the Crazyflie radio address, verifying connectivity, and enabling debugging access.

Note: A single tool may fulfill more than one requirement.

---

## 2. Requirements

### 2.1 General

| ID | Requirement |
|---|---|
| SS-001 | The system setup helpers shall run on Raspberry Pi with Raspbian OS as the primary target platform. |
| SS-002 | The system setup helpers shall be well modularized and easy to maintain. |
| SS-003 | Before each sudo call, the tool shall print a description of what the sudo command will do and wait for user confirmation. |
| SS-004 | Before each `git clone` call, the tool shall inform the user of the repository to be cloned and prompt for confirmation before proceeding. |

### 2.2 Crazyflie Configuration

| ID | Requirement |
|---|---|
| SS-010 | There shall be a tool to write the radio address to the Crazyflie over USB, equivalent to the "Configure 2.x" functionality in the Crazyflie client. |
| SS-011 | There shall be a tool to configure the Crazyflie URI to be used by Crazypilot. |
| SS-012 | There shall be a tool to verify that the configured Crazyflie URI is reachable (test connection). |

### 2.3 Service Setup

| ID | Requirement |
|---|---|
| SS-020 | There shall be a tool to set up all services necessary to fulfill the startup requirements (e.g. auto-starting Crazypilot on boot). |

### 2.4 Debugging Setup

| ID | Requirement |
|---|---|
| SS-030 | There shall be a tool to enable SSH access on the Raspberry Pi. |
