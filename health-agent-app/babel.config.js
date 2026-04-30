module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        'module-resolver',
        {
          root: ['./src'],
          alias: {
            '@app': './src/app',
            '@core': './src/core',
            '@features': './src/features',
            '@shared': './src/shared',
            '@assets': './src/assets',
          },
        },
      ],
      'react-native-reanimated/plugin',
    ],
  };
};
