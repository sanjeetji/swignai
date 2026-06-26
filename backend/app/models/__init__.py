"""SQLAlchemy models (blueprint/06). Importing this package registers all tables."""
from .user import User, Role, Permission, UserRole, RolePermission, PasswordResetToken  # noqa: F401
from .platform import (  # noqa: F401
    PlatformSetting, ThemePreset, UserPreference, FeatureFlag, Integration,
)
from .session import UserSession, LoginHistory, UserBlock  # noqa: F401
from .event import EventLog, DataSubjectRequest  # noqa: F401
from .trading import AIPick, PaperTrade, UserAnalytics, RegimeLog, BacktestRun  # noqa: F401
from .cms import (  # noqa: F401
    CmsPage, CmsSection, ContentCategory, ContentItem, Testimonial, StatMetric,
    Faq, NavigationMenu, MediaAsset, SeoMeta, ContentVersion,
)
from .billing import Subscription, Payment, Notification  # noqa: F401
from .referral import ReferralCode, Referral  # noqa: F401
