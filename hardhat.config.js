/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
    solidity: "0.8.28",
    networks: {
      hardhat: {
        chainId: 80001,
        accounts: {
          mnemonic: "test test test test test test test test test test test junk",
          path: "m/44'/60'/0'/0",
          count: 10,
          accountsBalance: "10000000000000000000000",
        }
      },
    },
  };
