import { defineModels } from '../schema';
import mistralMedium352604 from './mistral-medium-3-5-26-04';
import mistralSmall402603 from './mistral-small-4-0-26-03';
import mistralLarge42608 from './mistral-large-4-26-08';
import codestral2508 from './codestral-25-08';
import devstral22512 from './devstral-2-25-12';
export const MODELS = defineModels([
  mistralMedium352604,
  mistralSmall402603,
  mistralLarge42608,
  codestral2508,
  devstral22512,
] as const);

const checkDuplicates = (throwError = true) => {
  const set = new Set(MODELS.map(m => m.slug));
  const modelSlugs = MODELS.map(m => m.slug);
  if (modelSlugs.length !== set.size) {
    const duplicates = modelSlugs.filter(
      slug => modelSlugs.indexOf(slug) !== modelSlugs.lastIndexOf(slug)
    );
    const setOfDuplicates = Array.from(new Set(duplicates));
    if (throwError) {
      throw new Error(
        '[ERROR] Duplicated model slugs: ' + setOfDuplicates.join(', ')
      );
    }
    console.log('[WARN] Duplicated model slugs: ' + setOfDuplicates.join(', '));
  }
};
checkDuplicates(false);
