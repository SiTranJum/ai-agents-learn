/**
 * 素材路径常量定义
 * 统一管理所有图片资源的引用路径
 */

// Logo
export const Logo = {
  appIcon: require('../../assets/images/logo/app-icon.png'),
};

// 插画
export const Illustrations = {
  homePerson: require('../../assets/images/illustrations/home-person.png'),
  waterCup: require('../../assets/images/illustrations/water-cup.png'),
  exercise: require('../../assets/images/illustrations/exercise.png'),
  sleep: require('../../assets/images/illustrations/sleep.png'),
  loginHero: require('../../assets/images/illustrations/login-hero.png'),
};

// 空状态图
export const EmptyStates = {
  diet: require('../../assets/images/empty-states/empty-diet.png'),
  plan: require('../../assets/images/empty-states/empty-plan.png'),
  data: require('../../assets/images/empty-states/empty-data.png'),
};

// 统一导出
export const Images = {
  logo: Logo,
  illustrations: Illustrations,
  emptyStates: EmptyStates,
};
