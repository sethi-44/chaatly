import { softBg, getCardColor, getCardEmoji, CARD_COLORS, CARD_EMOJIS, C } from '../constants';

describe('Constants Utilities', () => {
  describe('softBg', () => {
    it('converts hex to rgba with default opacity', () => {
      expect(softBg('#FF2D78')).toBe('rgba(255,45,120,0.1)');
    });

    it('converts hex to rgba with custom opacity', () => {
      expect(softBg('#FF2D78', 0.5)).toBe('rgba(255,45,120,0.5)');
    });

    it('handles different hex colors', () => {
      expect(softBg('#00A699', 0.1)).toBe('rgba(0,166,153,0.1)');
      expect(softBg('#8B5CF6', 0.2)).toBe('rgba(139,92,246,0.2)');
      expect(softBg('#FFC629', 0.3)).toBe('rgba(255,198,41,0.3)');
    });

    it('handles lowercase hex', () => {
      expect(softBg('#ff2d78')).toBe('rgba(255,45,120,0.1)');
    });

    it('handles 3-digit hex (expanded)', () => {
      expect(softBg('#F00')).toBe('rgba(255,0,0,0.1)');
      expect(softBg('#0F0')).toBe('rgba(0,255,0,0.1)');
      expect(softBg('#00F')).toBe('rgba(0,0,255,0.1)');
    });
  });

  describe('getCardColor', () => {
    it('returns colors in sequence', () => {
      expect(getCardColor(0)).toBe(CARD_COLORS[0]);
      expect(getCardColor(1)).toBe(CARD_COLORS[1]);
      expect(getCardColor(2)).toBe(CARD_COLORS[2]);
    });

    it('wraps around using modulo', () => {
      expect(getCardColor(CARD_COLORS.length)).toBe(CARD_COLORS[0]);
      expect(getCardColor(CARD_COLORS.length + 1)).toBe(CARD_COLORS[1]);
      expect(getCardColor(CARD_COLORS.length * 2)).toBe(CARD_COLORS[0]);
    });

    it('handles negative indices', () => {
      expect(getCardColor(-1)).toBe(CARD_COLORS[CARD_COLORS.length - 1]);
      expect(getCardColor(-2)).toBe(CARD_COLORS[CARD_COLORS.length - 2]);
    });
  });

  describe('getCardEmoji', () => {
    it('returns emojis in sequence', () => {
      expect(getCardEmoji(0)).toBe(CARD_EMOJIS[0]);
      expect(getCardEmoji(1)).toBe(CARD_EMOJIS[1]);
      expect(getCardEmoji(2)).toBe(CARD_EMOJIS[2]);
    });

    it('wraps around using modulo', () => {
      expect(getCardEmoji(CARD_EMOJIS.length)).toBe(CARD_EMOJIS[0]);
      expect(getCardEmoji(CARD_EMOJIS.length + 1)).toBe(CARD_EMOJIS[1]);
    });

    it('handles negative indices', () => {
      expect(getCardEmoji(-1)).toBe(CARD_EMOJIS[CARD_EMOJIS.length - 1]);
    });
  });

  describe('CARD_COLORS', () => {
    it('has expected colors', () => {
      expect(CARD_COLORS).toHaveLength(6);
      expect(CARD_COLORS).toContain('#FFEBF0');
      expect(CARD_COLORS).toContain('#FFF0E6');
      expect(CARD_COLORS).toContain('#F0E6FF');
      expect(CARD_COLORS).toContain('#E6FFF0');
      expect(CARD_COLORS).toContain('#FFF5E6');
      expect(CARD_COLORS).toContain('#E6F0FF');
    });
  });

  describe('CARD_EMOJIS', () => {
    it('has expected emojis', () => {
      expect(CARD_EMOJIS).toHaveLength(10);
      expect(CARD_EMOJIS).toContain('🍕');
      expect(CARD_EMOJIS).toContain('🌮');
      expect(CARD_EMOJIS).toContain('🍜');
      expect(CARD_EMOJIS).toContain('🥘');
      expect(CARD_EMOJIS).toContain('🍣');
      expect(CARD_EMOJIS).toContain('🧆');
      expect(CARD_EMOJIS).toContain('🥗');
      expect(CARD_EMOJIS).toContain('🍲');
      expect(CARD_EMOJIS).toContain('🫕');
      expect(CARD_EMOJIS).toContain('🥂');
    });
  });

  describe('Color Constants', () => {
    it('has all required color properties', () => {
      expect(C.primary).toBe('#FF2D78');
      expect(C.accent).toBe('#FFC629');
      expect(C.purple).toBe('#8B5CF6');
      expect(C.success).toBe('#00A699');
      expect(C.error).toBe('#E31C5F');
      expect(C.bg).toBe('#FFFDF9');
      expect(C.text).toBe('#222222');
    });
  });
});