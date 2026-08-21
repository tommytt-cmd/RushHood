# Wallet Module

This module encapsulates blockchain wallet connectivity, chain management, contract instantiation, transaction handling, and ERC20 token utilities.

## Architecture

- `WalletProvider` exposes wallet and chain state through React Context.
- `useWallet`, `useProvider`, `useSigner`, `useChain`, `useBalances` are hooks for safe consumer access.
- `WalletService` performs wallet connect/disconnect, detects installed wallets, and manages stored connector state.
- `ChainService` is responsible for network verification, switching, and chain metadata.
- `ContractFactory` provides a reusable contract creation layer with caching.
- `TransactionService` normalizes user-friendly transaction error handling.
- `TokenService` handles ERC20 balance, allowance, approvals, and value formatting.

## Wallet lifecycle

1. `WalletProvider` attempts automatic reconnection for stored connector data.
2. `connect()` requests wallet access via browser provider.
3. `disconnect()` clears local state and stored connector.
4. `accountsChanged`, `chainChanged`, `disconnect` events update React state immediately.

## Connection flow

- `WalletProvider.connect()` invokes `WalletService.connect()`.
- On success, provider and signer are initialized and wallet state is populated.
- Network and balance information are refreshed automatically.

## Future integration

- Use `ContractFactory.createContract()` to build typed contract instances.
- Use `TransactionService.sendTransaction()` to submit and wait for tx receipts.
- Use `TokenService` for ERC20 token operations.
- Add new connectors in `connectors.ts` without changing UI components.
